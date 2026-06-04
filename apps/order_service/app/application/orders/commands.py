from dataclasses import dataclass
from uuid import uuid4

from apps.order_service.app.domain.entities import Order, OrderItemEntity
from apps.order_service.app.domain.value_objects import Money, OrderStatusState
from apps.order_service.app.infrastructure.config.settings import settings
from apps.order_service.app.infrastructure.observability.logging import get_logger
from apps.order_service.app.infrastructure.observability.metrics import (
    order_created_total,
    rabbitmq_message_published_total,
)
from apps.order_service.app.infrastructure.observability.tracing import (
    add_span_attributes,
)
from apps.order_service.app.schemas import OrderCreatedEvent, OrderCreatedPayload
from apps.order_service.app.schemas.topics import RoutingKey

logger = get_logger(__name__)


@dataclass(frozen=True)
class CreatedOrder:
    order_id: str
    status: str


async def create_order_for_user(user_id: str) -> CreatedOrder:
    from apps.order_service.app.application import services as services_module

    order_id = uuid4()
    cart_id = f"cart_{user_id}"
    cart = services_module.get_cart_snapshot(user_id)
    currency = "USD"

    items = tuple(
        OrderItemEntity(
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=Money(item.unit_price, currency),
            currency=currency,
        )
        for item in cart.items
    )
    order = Order.create(
        order_id=order_id,
        user_id=user_id,
        cart_id=cart_id,
        total_amount=Money(cart.total_amount, currency),
        items=items,
        currency=currency,
    )

    event = OrderCreatedEvent(
        payload=OrderCreatedPayload(
            order_id=order_id,
            user_id=user_id,
            cart_id=cart_id,
            amount=order.total_amount.amount,
            currency=order.total_amount.currency,
        )
    )

    await services_module.save_order_with_outbox(
        order_id=order_id,
        user_id=user_id,
        cart_id=cart_id,
        status=OrderStatusState.PENDING,
        total_amount=order.total_amount.amount,
        currency=order.total_amount.currency,
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

    await services_module.publish_pending_order_events(limit=10)

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
        status=OrderStatusState.PENDING,
    )


async def save_order_status(order_id: str, status: str) -> None:
    from apps.order_service.app.application import services as services_module
    from apps.order_service.app.application.orders.queries import _parse_order_id
    from apps.order_service.app.domain.entities import Order
    from apps.order_service.app.domain.value_objects import Money, OrderStatusState

    parsed_order_id = _parse_order_id(order_id)
    if parsed_order_id is None:
        return

    order_record = await services_module.get_order_record_by_id(parsed_order_id)
    if order_record is None:
        return

    order = Order(
        order_id=parsed_order_id,
        user_id=order_record.user_id,
        status=order_record.status,
        total_amount=Money.zero(),
    )
    desired_status = OrderStatusState.from_value(status)

    if desired_status == OrderStatusState.PENDING:
        return
    if desired_status == OrderStatusState.PAYMENT_PROCESSING:
        order.pay()
    elif desired_status == OrderStatusState.CONFIRMED:
        order.confirm()
    elif desired_status == OrderStatusState.CANCELLED:
        order.cancel()
    elif desired_status == OrderStatusState.FAILED:
        order.fail()
    else:
        order.transition_to(desired_status)

    await services_module.update_order_status(parsed_order_id, order.status.value)
