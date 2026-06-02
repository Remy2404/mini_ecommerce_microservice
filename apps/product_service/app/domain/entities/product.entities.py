"""Pure product domain entities."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class ProductEntity:
    product_id: UUID
    name: str
    price: Decimal
    stock_quantity: int
    category: str
    image_object_key: str | None = None


@dataclass(frozen=True)
class CategoryEntity:
    category_id: UUID
    name: str
    description: str | None = None
