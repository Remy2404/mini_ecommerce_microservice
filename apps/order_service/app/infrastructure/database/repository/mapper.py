from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence
from uuid import UUID, uuid4

from apps.order_service.app.domain.entities import Order as OrderAggregate
from apps.order_service.app.domain.entities import OrderItemEntity
from apps.order_service.app.domain.value_objects import Money, OrderStatusState
from apps.order_service.app.infrastructure.clients.cart_client import CartSnapshotItem
from apps.order_service.app.infrastructure.database.models import Order as OrderModel
from apps.order_service.app.infrastructure.database.models import OrderItem


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
