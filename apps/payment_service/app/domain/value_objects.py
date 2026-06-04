"""Payment Service value objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar
from uuid import UUID, uuid4

from apps.payment_service.app.domain.exceptions import (
    InvalidPaymentStateTransitionException,
)


def _to_decimal(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


@dataclass(frozen=True, slots=True)
class PaymentId:
    value: UUID

    @classmethod
    def new(cls) -> "PaymentId":
        return cls(uuid4())

    @classmethod
    def from_value(cls, value: PaymentId | UUID | str) -> "PaymentId":
        if isinstance(value, PaymentId):
            return value
        return cls(UUID(str(value)))

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PaymentId):
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
class PaymentStatusState:
    value: str

    PENDING: ClassVar[str] = "PENDING"
    SUCCESS: ClassVar[str] = "SUCCESS"
    FAILED: ClassVar[str] = "FAILED"
    REFUNDED: ClassVar[str] = "REFUNDED"

    _ALLOWED_VALUES: ClassVar[set[str]] = {
        PENDING,
        SUCCESS,
        FAILED,
        REFUNDED,
    }
    _TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        PENDING: {SUCCESS, FAILED},
        SUCCESS: {REFUNDED},
        FAILED: set(),
        REFUNDED: set(),
    }

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if normalized not in self._ALLOWED_VALUES:
            raise ValueError(f"Invalid payment status: {self.value!r}")
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_value(cls, value: PaymentStatusState | str) -> "PaymentStatusState":
        if isinstance(value, PaymentStatusState):
            return value
        return cls(value)

    @classmethod
    def pending(cls) -> "PaymentStatusState":
        return cls(cls.PENDING)

    @classmethod
    def success(cls) -> "PaymentStatusState":
        return cls(cls.SUCCESS)

    @classmethod
    def failed(cls) -> "PaymentStatusState":
        return cls(cls.FAILED)

    @classmethod
    def refunded(cls) -> "PaymentStatusState":
        return cls(cls.REFUNDED)

    @property
    def is_terminal(self) -> bool:
        return self.value in {self.SUCCESS, self.FAILED, self.REFUNDED}

    def can_transition_to(self, next_state: PaymentStatusState | str) -> bool:
        next_value = self.from_value(next_state).value
        return next_value == self.value or next_value in self._TRANSITIONS[self.value]

    def transition_to(self, next_state: PaymentStatusState | str) -> "PaymentStatusState":
        next_value = self.from_value(next_state)
        if next_value == self:
            return self
        if not self.can_transition_to(next_value):
            raise InvalidPaymentStateTransitionException(
                f"Cannot transition payment from {self.value} to {next_value.value}"
            )
        return next_value

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PaymentStatusState):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip().upper()
        return NotImplemented  # type: ignore[return-value]
