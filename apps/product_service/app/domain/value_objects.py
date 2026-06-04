"""Product Service value objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class ProductId:
    value: UUID

    @classmethod
    def new(cls) -> "ProductId":
        return cls(uuid4())

    @classmethod
    def from_value(cls, value: ProductId | UUID | str) -> "ProductId":
        if isinstance(value, ProductId):
            return value
        return cls(UUID(str(value)))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class CategoryId:
    value: UUID

    @classmethod
    def new(cls) -> "CategoryId":
        return cls(uuid4())

    @classmethod
    def from_value(cls, value: CategoryId | UUID | str) -> "CategoryId":
        if isinstance(value, CategoryId):
            return value
        return cls(UUID(str(value)))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        currency = self.currency.strip().upper()
        if not currency:
            raise ValueError("Currency cannot be empty")
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "amount", Decimal(str(self.amount)).quantize(Decimal("0.01")))

    @classmethod
    def from_value(
        cls,
        value: Money | Decimal | int | str,
        *,
        currency: str = "USD",
    ) -> "Money":
        if isinstance(value, Money):
            if value.currency != currency.strip().upper():
                raise ValueError("Currency mismatch")
            return value
        return cls(Decimal(str(value)), currency)

    def __add__(self, other: Money) -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount + other.amount, self.currency)

    def __radd__(self, other: object) -> "Money":
        if other == 0:
            return self
        if isinstance(other, Money):
            return other + self
        return NotImplemented  # type: ignore[return-value]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Money):
            return self.amount == other.amount and self.currency == other.currency
        if isinstance(other, Decimal):
            return self.amount == Decimal(str(other)).quantize(Decimal("0.01"))
        if isinstance(other, (int, str)):
            return self.amount == Decimal(str(other)).quantize(Decimal("0.01"))
        return NotImplemented  # type: ignore[return-value]
