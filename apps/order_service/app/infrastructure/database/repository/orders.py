from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence
from uuid import UUID, uuid4

from sqlalchemy import delete

from apps.order_service.app.domain.entities import Order as OrderAggregate
from apps.order_service.app.domain.entities import OrderItemEntity
from apps.order_service.app.domain.value_objects import Money, OrderStatusState
from apps.order_service.app.infrastructure.clients.cart_client import CartSnapshotItem
from apps.order_service.app.infrastructure.config.settings import settings
from apps.order_service.app.infrastructure.database.models import (
    InboxEvent,
    Order as OrderModel,
    OrderItem,
    OutboxEvent,
)
from apps.order_service.app.infrastructure.database.session import session_scope


@dataclass(slots=True)
class OrderMapper:
    @staticmethod
    def to_domain(
        order: OrderModel,
        items: Sequence[OrderItem] | None = None,
    ) -> OrderAggregate:
        order_items = items if items is not None else order.items
        return OrderAggregate(
            order_id=order.id,
            user_id=order.user_id,
            cart_id=order.cart_id,
            status=OrderStatusState.from_value(order.status),
            total_amount=Money(order.total_amount, order.currency),
            items=tuple(
                OrderItemEntity(
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=Money(item.unit_price, order.currency),
                    currency=order.currency,
                )
                for item in order_items
            ),
            currency=order.currency,
            correlation_id=order.correlation_id,
            shipping_address=order.shipping_address,
        )

    @staticmethod
    def to_model(order: OrderAggregate) -> OrderModel:
        return OrderModel(
            id=order.order_id.value,
            user_id=order.user_id,
            cart_id=order.cart_id,
            status=order.status.value,
            total_amount=order.total_amount.amount,
            currency=order.total_amount.currency,
            shipping_address=order.shipping_address,
            correlation_id=order.correlation_id,
        )

    @staticmethod
    def sync_items(order_model: OrderModel, order: OrderAggregate) -> None:
        order_model.items.clear()
        for item in order.items:
            order_model.items.append(
                OrderItem(
                    id=uuid4(),
                    order_id=order.order_id.value,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price.amount,
                    subtotal=item.subtotal.amount,
                )
            )

    @staticmethod
    def from_cart_items(
        *,
        order_id: UUID,
        user_id: str,
        cart_id: str,
        total_amount: Decimal,
        currency: str,
        correlation_id: str,
        items: list[CartSnapshotItem],
        status: str,
        shipping_address: str | None = None,
    ) -> OrderAggregate:
        order = OrderAggregate.create(
            order_id=order_id,
            user_id=user_id,
            cart_id=cart_id,
            total_amount=Money(total_amount, currency),
            items=tuple(
                OrderItemEntity(
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=Money(item.unit_price, currency),
                    currency=currency,
                )
                for item in items
            ),
            currency=currency,
            correlation_id=correlation_id,
            shipping_address=shipping_address,
        )
        desired_status = OrderStatusState.from_value(status)
        if desired_status != order.status:
            order.transition_to(desired_status)
        return order


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
        desired_status = OrderStatusState.from_value(status)
        order.transition_to(desired_status)

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
            desired_status = OrderStatusState.from_value(status)
            order.transition_to(desired_status)
            order_model.status = order.status.value
            order_model.total_amount = order.total_amount.amount
            order_model.currency = order.total_amount.currency
            order_model.shipping_address = order.shipping_address
            order_model.correlation_id = order.correlation_id

    return True
