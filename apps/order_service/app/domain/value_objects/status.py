from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from apps.order_service.app.domain.exceptions import InvalidStateTransitionException


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
