"""Product Service domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from apps.product_service.app.domain.policies import ensure_product_values
from apps.product_service.app.domain.value_objects import CategoryId, Money, ProductId


@dataclass(slots=True)
class ProductEntity:
    product_id: ProductId | UUID
    name: str
    description: str | None
    price: Money | Decimal
    stock_quantity: int
    category: str
    image_object_key: str | None = None

    def __post_init__(self) -> None:
        self.product_id = ProductId.from_value(self.product_id)
        self.price = Money.from_value(self.price)
        self.name = self.name.strip()
        if self.description is not None:
            self.description = self.description.strip() or None
        self.category = self.category.strip()
        ensure_product_values(price=self.price.amount, stock_quantity=self.stock_quantity)
        if not self.name:
            raise ValueError("Product name cannot be empty")
        if not self.category:
            raise ValueError("Product category cannot be empty")

    def with_image_object_key(self, object_key: str | None) -> "ProductEntity":
        return ProductEntity(
            product_id=self.product_id,
            name=self.name,
            description=self.description,
            price=self.price,
            stock_quantity=self.stock_quantity,
            category=self.category,
            image_object_key=object_key,
        )


@dataclass(slots=True)
class CategoryEntity:
    category_id: CategoryId | UUID
    name: str
    description: str | None = None

    def __post_init__(self) -> None:
        self.category_id = CategoryId.from_value(self.category_id)
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Category name cannot be empty")
        if self.description is not None:
            self.description = self.description.strip() or None

