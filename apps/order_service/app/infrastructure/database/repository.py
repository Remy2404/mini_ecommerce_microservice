"""Order repository using SQLAlchemy async ORM."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import delete, or_, select

from apps.order_service.app.infrastructure.clients.cart_client import CartSnapshotItem
from apps.order_service.app.infrastructure.database.models import (
    InboxEvent,
    Order,
    OrderItem,
    OutboxEvent,
)
from packages.config.settings import settings
from packages.database.session import session_scope


@dataclass(frozen=True)
class PendingOutboxEvent:
    event_id: str
    event_type: str
    routing_key: str
    payload: dict
    attempts: int


@dataclass(frozen=True)
class OrderRecord:
    order_id: UUID
    user_id: str
    status: str


async def save_order(
    *,
    order_id: UUID,
    user_id: str,
    cart_id: str,
    status: str,
    total_amount: Decimal,
    currency: str,
    correlation_id: str,
    items: list[CartSnapshotItem],
) -> None:
    async with session_scope(settings.orders_database_url) as session:
        order = await session.get(Order, order_id)
        if order is None:
            order = Order(
                id=order_id,
                user_id=user_id,
                cart_id=cart_id,
                status=str(status),
                total_amount=total_amount,
                currency=currency,
                correlation_id=correlation_id,
            )
            session.add(order)
        else:
            order.status = str(status)
            order.total_amount = total_amount
            order.currency = currency
            order.correlation_id = correlation_id

        await session.execute(delete(OrderItem).where(OrderItem.order_id == order_id))
        for item in items:
            session.add(
                OrderItem(
                    id=uuid4(),
                    order_id=order_id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                )
            )


async def save_order_with_outbox(
    *,
    order_id: UUID,
    user_id: str,
    cart_id: str,
    status: str,
    total_amount: Decimal,
    currency: str,
    correlation_id: str,
    items: list[CartSnapshotItem],
    event_id: str,
    event_type: str,
    routing_key: str,
    event_payload: dict,
    trace_id: str | None,
) -> None:
    async with session_scope(settings.orders_database_url) as session:
        order = Order(
            id=order_id,
            user_id=user_id,
            cart_id=cart_id,
            status=str(status),
            total_amount=total_amount,
            currency=currency,
            correlation_id=correlation_id,
        )
        session.add(order)

        for item in items:
            session.add(
                OrderItem(
                    id=uuid4(),
                    order_id=order_id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                )
            )

        session.add(
            OutboxEvent(
                event_id=event_id,
                event_type=event_type,
                routing_key=routing_key,
                payload=event_payload,
                correlation_id=correlation_id,
                trace_id=trace_id,
            )
        )


async def update_order_status(order_id: UUID, status: str) -> None:
    async with session_scope(settings.orders_database_url) as session:
        order = await session.get(Order, order_id)
        if order is not None:
            order.status = str(status)


async def apply_payment_result_once(
    *,
    event_id: str,
    event_type: str,
    order_id: UUID,
    status: str,
    consumer_name: str = "order.payment_result_consumer",
) -> bool:
    async with session_scope(settings.orders_database_url) as session:
        if await session.get(InboxEvent, event_id) is not None:
            return False

        session.add(
            InboxEvent(
                event_id=event_id,
                event_type=event_type,
                consumer_name=consumer_name,
            )
        )

        order = await session.get(Order, order_id)
        if order is not None:
            order.status = str(status)

    return True


async def claim_pending_outbox_events(limit: int = 25) -> list[PendingOutboxEvent]:
    now = datetime.now(UTC)
    async with session_scope(settings.orders_database_url) as session:
        result = await session.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.status.in_(("PENDING", "FAILED")),
                or_(
                    OutboxEvent.next_attempt_at.is_(None),
                    OutboxEvent.next_attempt_at <= now,
                ),
            )
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
        )
        events = result.scalars().all()

        for event in events:
            event.status = "IN_PROGRESS"
            event.attempts += 1
            event.updated_at = now

        return [
            PendingOutboxEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                routing_key=event.routing_key,
                payload=event.payload,
                attempts=event.attempts,
            )
            for event in events
        ]


async def mark_outbox_event_published(event_id: str) -> None:
    async with session_scope(settings.orders_database_url) as session:
        event = await session.get(OutboxEvent, event_id)
        if event is not None:
            event.status = "PUBLISHED"
            event.published_at = datetime.now(UTC)
            event.updated_at = datetime.now(UTC)


async def mark_outbox_event_failed(
    event_id: str,
    error: str,
    *,
    retry_delay_seconds: int = 30,
) -> None:
    async with session_scope(settings.orders_database_url) as session:
        event = await session.get(OutboxEvent, event_id)
        if event is not None:
            now = datetime.now(UTC)
            event.status = "FAILED"
            event.last_error = error[:1000]
            event.next_attempt_at = now + timedelta(seconds=retry_delay_seconds)
            event.updated_at = now


async def get_order_status_by_id(order_id: UUID) -> str | None:
    async with session_scope(settings.orders_database_url) as session:
        order = await session.get(Order, order_id)

    return str(order.status) if order else None


async def get_order_record_by_id(order_id: UUID) -> OrderRecord | None:
    async with session_scope(settings.orders_database_url) as session:
        order = await session.get(Order, order_id)

    if order is None:
        return None

    return OrderRecord(
        order_id=order.id,
        user_id=order.user_id,
        status=str(order.status),
    )


async def list_order_statuses(user_id: str | None = None) -> dict[str, str]:
    async with session_scope(settings.orders_database_url) as session:
        query = select(Order)
        if user_id is not None:
            query = query.where(Order.user_id == user_id)
        result = await session.execute(
            query.order_by(Order.created_at.desc(), Order.id.desc())
        )
        orders = result.scalars().all()

    return {str(order.id): str(order.status) for order in orders}


async def clear_orders() -> None:
    async with session_scope(settings.orders_database_url) as session:
        await session.execute(delete(Order))
