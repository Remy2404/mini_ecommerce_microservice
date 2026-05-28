"""Pure order domain entities."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class OrderItemEntity:
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class OrderEntity:
    order_id: UUID
    user_id: str
    status: str
    items: tuple[OrderItemEntity, ...]

    @property
    def total_amount(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))
