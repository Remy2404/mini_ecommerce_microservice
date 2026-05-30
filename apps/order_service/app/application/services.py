from dataclasses import dataclass
import json
from uuid import UUID
from uuid import uuid4

from apps.order_service.app.infrastructure.clients.cart_client import get_cart_snapshot
from apps.order_service.app.infrastructure.database.repository import (
    clear_orders,
    get_order_record_by_id,
    get_order_status_by_id,
    list_order_statuses,
    save_order_with_outbox,
    update_order_status,
)
from apps.order_service.app.infrastructure.messaging.outbox_publisher import (
    publish_pending_order_events,
)
from packages.config.settings import settings
from packages.contracts.order.events import OrderCreatedEvent, OrderCreatedPayload
from packages.contracts.common.schemas import OrderStatus
from packages.contracts.order.topics import RoutingKey
from packages.errors.exceptions import ForbiddenError
from packages.observability.logging import get_logger
from packages.observability.metrics import (
    order_created_total,
    rabbitmq_message_published_total,
)
from packages.observability.tracing import add_span_attributes


logger = get_logger(__name__)


@dataclass(frozen=True)
class CreatedOrder:
    order_id: str
    status: OrderStatus


async def create_order_for_user(user_id: str) -> CreatedOrder:
    order_id = uuid4()
    cart_id = f"cart_{user_id}"
    cart = get_cart_snapshot(user_id)

    event = OrderCreatedEvent(
        payload=OrderCreatedPayload(
            order_id=order_id,
            user_id=user_id,
            cart_id=cart_id,
            amount=cart.total_amount,
        )
    )

    await save_order_with_outbox(
        order_id=order_id,
        user_id=user_id,
        cart_id=cart_id,
        status=OrderStatus.PENDING,
        total_amount=cart.total_amount,
        currency=event.payload.currency,
        correlation_id=event.correlation_id,
        items=cart.items,
        event_id=event.event_id,
        event_type=event.event_type,
        routing_key=RoutingKey.ORDER_CREATED,
        event_payload=event.model_dump(mode="json"),
        trace_id=event.trace_id,
    )

    add_span_attributes(
        {
            "order.id": str(order_id),
            "user.id": user_id,
            "event.type": event.event_type,
        }
    )

    await publish_pending_order_events(limit=10)

    order_created_total.labels(
        service_name=settings.order_service_name,
    ).inc()

    rabbitmq_message_published_total.labels(
        service_name=settings.order_service_name,
        routing_key=RoutingKey.ORDER_CREATED,
    ).inc()

    logger.info(
        "Order created event persisted to outbox",
        order_id=str(order_id),
        user_id=user_id,
        routing_key=RoutingKey.ORDER_CREATED,
    )

    return CreatedOrder(
        order_id=str(order_id),
        status=OrderStatus.PENDING,
    )


def _parse_order_id(order_id: str) -> UUID | None:
    try:
        return UUID(order_id)
    except ValueError:
        return None


async def save_order_status(order_id: str, status: str) -> None:
    parsed_order_id = _parse_order_id(order_id)
    if parsed_order_id is None:
        return

    await update_order_status(parsed_order_id, status)


async def get_order_status(order_id: str, *, user_id: str | None = None) -> str | None:
    parsed_order_id = _parse_order_id(order_id)
    if parsed_order_id is None:
        return None

    if user_id is not None:
        order = await get_order_record_by_id(parsed_order_id)
        if order is None:
            return None
        if order.user_id != user_id:
            raise ForbiddenError
        return order.status

    return await get_order_status_by_id(parsed_order_id)


async def get_all_orders(user_id: str | None = None) -> dict[str, str]:
    return await list_order_statuses(user_id=user_id)


async def clear_order_state() -> None:
    await clear_orders()


async def dump_order_state() -> str:
    return json.dumps(
        await get_all_orders(),
        indent=2,
        sort_keys=True,
    )
