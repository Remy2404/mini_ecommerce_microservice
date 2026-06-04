from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


def _to_decimal(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        currency = self.currency.strip().upper()
        if not currency:
            raise ValueError("Currency cannot be empty")
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "amount", _to_decimal(self.amount))

    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        return cls(Decimal("0"), currency)

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

    def __mul__(self, multiplier: int) -> "Money":
        return Money(self.amount * Decimal(str(multiplier)), self.currency)

    def __rmul__(self, multiplier: int) -> "Money":
        return self * multiplier

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Money):
            return self.amount == other.amount and self.currency == other.currency
        if isinstance(other, Decimal):
            return self.amount == _to_decimal(other)
        if isinstance(other, (int, str)):
            return self.amount == _to_decimal(other)
        return NotImplemented  # type: ignore[return-value]
