"""Order Service value objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar
from uuid import UUID, uuid4

from apps.order_service.app.domain.exceptions import (
    InvalidStateTransitionException,
)


def _to_decimal(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


@dataclass(frozen=True, slots=True)
class OrderId:
    value: UUID

    @classmethod
    def new(cls) -> "OrderId":
        return cls(uuid4())

    @classmethod
    def from_value(cls, value: OrderId | UUID | str) -> "OrderId":
        if isinstance(value, OrderId):
            return value
        return cls(UUID(str(value)))

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OrderId):
            return self.value == other.value
        if isinstance(other, UUID):
            return self.value == other
        if isinstance(other, str):
            return str(self.value) == other
        return NotImplemented  # type: ignore[return-value]


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


@dataclass(frozen=True, slots=True)
class OrderStatusState:
    value: str

    PENDING: ClassVar[str] = "PENDING"
    PAYMENT_PROCESSING: ClassVar[str] = "PAYMENT_PROCESSING"
    CONFIRMED: ClassVar[str] = "CONFIRMED"
    CANCELLED: ClassVar[str] = "CANCELLED"
    FAILED: ClassVar[str] = "FAILED"

    _ALLOWED_VALUES: ClassVar[set[str]] = {
        PENDING,
        PAYMENT_PROCESSING,
        CONFIRMED,
        CANCELLED,
        FAILED,
    }
    _TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        PENDING: {PAYMENT_PROCESSING, CONFIRMED, CANCELLED, FAILED},
        PAYMENT_PROCESSING: {CONFIRMED, CANCELLED, FAILED},
        CONFIRMED: set(),
        CANCELLED: set(),
        FAILED: set(),
    }

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if normalized not in self._ALLOWED_VALUES:
            raise ValueError(f"Invalid order status: {self.value!r}")
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_value(cls, value: OrderStatusState | str) -> "OrderStatusState":
        if isinstance(value, OrderStatusState):
            return value
        return cls(value)

    @classmethod
    def pending(cls) -> "OrderStatusState":
        return cls(cls.PENDING)

    @classmethod
    def payment_processing(cls) -> "OrderStatusState":
        return cls(cls.PAYMENT_PROCESSING)

    @classmethod
    def confirmed(cls) -> "OrderStatusState":
        return cls(cls.CONFIRMED)

    @classmethod
    def cancelled(cls) -> "OrderStatusState":
        return cls(cls.CANCELLED)

    @classmethod
    def failed(cls) -> "OrderStatusState":
        return cls(cls.FAILED)

    @property
    def is_terminal(self) -> bool:
        return self.value in {self.CONFIRMED, self.CANCELLED, self.FAILED}

    def can_transition_to(self, next_state: OrderStatusState | str) -> bool:
        next_value = self.from_value(next_state).value
        return next_value == self.value or next_value in self._TRANSITIONS[self.value]

    def transition_to(self, next_state: OrderStatusState | str) -> "OrderStatusState":
        next_value = self.from_value(next_state)
        if next_value == self:
            return self
        if not self.can_transition_to(next_value):
            raise InvalidStateTransitionException(
                f"Cannot transition order from {self.value} to {next_value.value}"
            )
        return next_value

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OrderStatusState):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip().upper()
        return NotImplemented  # type: ignore[return-value]
