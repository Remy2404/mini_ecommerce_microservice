from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import delete

from apps.order_service.app.infrastructure.clients.cart_client import CartSnapshotItem
from apps.order_service.app.infrastructure.config.settings import settings
from apps.order_service.app.infrastructure.database.models import (
    InboxEvent,
    Order as OrderModel,
    OrderItem,
    OutboxEvent,
)
from apps.order_service.app.infrastructure.database.repository.mapper import OrderMapper
from apps.order_service.app.infrastructure.database.session import session_scope
from apps.order_service.app.domain.value_objects import OrderStatusState


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
        order = OrderMapper.from_cart_items(
            order_id=order_id,
            user_id=user_id,
            cart_id=cart_id,
            total_amount=total_amount,
            currency=currency,
            correlation_id=correlation_id,
            items=items,
            status=status,
        )
        order_model = await session.get(OrderModel, order_id)
        if order_model is None:
            order_model = OrderMapper.to_model(order)
            session.add(order_model)
        else:
            order_model.user_id = order.user_id
            order_model.cart_id = order.cart_id
            order_model.status = order.status.value
            order_model.total_amount = order.total_amount.amount
            order_model.currency = order.total_amount.currency
            order_model.shipping_address = order.shipping_address
            order_model.correlation_id = order.correlation_id

        await session.execute(delete(OrderItem).where(OrderItem.order_id == order_id))
        OrderMapper.sync_items(order_model, order)


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
        order = OrderMapper.from_cart_items(
            order_id=order_id,
            user_id=user_id,
            cart_id=cart_id,
            total_amount=total_amount,
            currency=currency,
            correlation_id=correlation_id,
            items=items,
            status=status,
        )
        session.add(OrderMapper.to_model(order))
        await session.flush()

        for item in order.items:
            session.add(
                OrderItem(
                    id=uuid4(),
                    order_id=order_id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price.amount,
                    subtotal=item.subtotal.amount,
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
        order_model = await session.get(OrderModel, order_id)
        if order_model is None:
            return

        order = OrderMapper.to_domain(order_model)
        order.transition_to(OrderStatusState.from_value(status))

        order_model.status = order.status.value
        order_model.total_amount = order.total_amount.amount
        order_model.currency = order.total_amount.currency
        order_model.shipping_address = order.shipping_address
        order_model.correlation_id = order.correlation_id


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

        order_model = await session.get(OrderModel, order_id)
        if order_model is not None:
            order = OrderMapper.to_domain(order_model)
            order.transition_to(OrderStatusState.from_value(status))
            order_model.status = order.status.value
            order_model.total_amount = order.total_amount.amount
            order_model.currency = order.total_amount.currency
            order_model.shipping_address = order.shipping_address
            order_model.correlation_id = order.correlation_id

    return True
