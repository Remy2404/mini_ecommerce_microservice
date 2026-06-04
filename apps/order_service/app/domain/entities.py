"""Pure order domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from apps.order_service.app.domain.policies import ensure_cart_can_be_ordered
from apps.order_service.app.domain.value_objects import Money, OrderId, OrderStatusState


def _item_value(item: object, key: str) -> object:
    if isinstance(item, dict):
        return item[key]
    return getattr(item, key)


@dataclass(slots=True)
class OrderItemEntity:
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Money | Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if not isinstance(self.product_id, UUID):
            self.product_id = UUID(str(self.product_id))
        self.unit_price = Money.from_value(self.unit_price, currency=self.currency)
        self.currency = self.unit_price.currency

    @property
    def subtotal(self) -> Money:
        return self.unit_price * self.quantity


@dataclass(slots=True)
class Order:
    order_id: OrderId | UUID
    user_id: str
    cart_id: str = ""
    status: OrderStatusState | str = field(default_factory=OrderStatusState.pending)
    total_amount: Money | Decimal = field(default_factory=Money.zero)
    items: tuple[OrderItemEntity, ...] = field(default_factory=tuple)
    currency: str = "USD"
    correlation_id: str = ""
    shipping_address: str | None = None

    def __post_init__(self) -> None:
        self.order_id = OrderId.from_value(self.order_id)
        self.status = OrderStatusState.from_value(self.status)
        self.total_amount = Money.from_value(self.total_amount, currency=self.currency)
        self.currency = self.total_amount.currency
        self.items = tuple(
            item
            if isinstance(item, OrderItemEntity)
            else OrderItemEntity(
                product_id=_item_value(item, "product_id"),
                product_name=_item_value(item, "product_name"),
                quantity=_item_value(item, "quantity"),
                unit_price=_item_value(item, "unit_price"),
                currency=self.currency,
            )
            for item in self.items
        )

    @classmethod
    def create(
        cls,
        *,
        order_id: OrderId | UUID | None = None,
        user_id: str,
        cart_id: str,
        total_amount: Money | Decimal,
        items: tuple[OrderItemEntity, ...],
        currency: str = "USD",
        correlation_id: str = "",
        shipping_address: str | None = None,
    ) -> "Order":
        ensure_cart_can_be_ordered(
            total_amount=Money.from_value(total_amount, currency=currency).amount,
            items_count=len(items),
        )
        actual_total = sum((item.subtotal for item in items), Money.zero(currency))
        expected_total = Money.from_value(total_amount, currency=currency)
        if actual_total != expected_total:
            raise ValueError("Order total must match item subtotals")
        return cls(
            order_id=order_id or OrderId.new(),
            user_id=user_id,
            cart_id=cart_id,
            status=OrderStatusState.pending(),
            total_amount=total_amount,
            items=items,
            currency=currency,
            correlation_id=correlation_id,
            shipping_address=shipping_address,
        )

    @property
    def amount(self) -> Money:
        return self.total_amount

    def transition_to(self, next_status: OrderStatusState | str) -> None:
        self.status = self.status.transition_to(next_status)

    def pay(self) -> None:
        self.transition_to(OrderStatusState.payment_processing())

    def confirm(self) -> None:
        self.transition_to(OrderStatusState.confirmed())

    def cancel(self) -> None:
        self.transition_to(OrderStatusState.cancelled())

    def fail(self) -> None:
        self.transition_to(OrderStatusState.failed())


OrderEntity = Order

