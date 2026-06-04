"""Pure payment domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from apps.payment_service.app.domain.policies import ensure_payable_amount
from apps.payment_service.app.domain.value_objects import (
    Money,
    PaymentId,
    PaymentStatusState,
)


@dataclass(slots=True)
class Payment:
    payment_id: PaymentId | UUID
    order_id: UUID
    user_id: str
    amount: Money | Decimal
    currency: str = "USD"
    status: PaymentStatusState | str = field(default_factory=PaymentStatusState.pending)
    failure_reason: str | None = None
    correlation_id: str = ""

    def __post_init__(self) -> None:
        self.payment_id = PaymentId.from_value(self.payment_id)
        self.status = PaymentStatusState.from_value(self.status)
        self.amount = Money.from_value(self.amount, currency=self.currency)
        self.currency = self.amount.currency
        ensure_payable_amount(self.amount.amount)
        if not isinstance(self.order_id, UUID):
            self.order_id = UUID(str(self.order_id))
        self.user_id = str(self.user_id)
        self.correlation_id = str(self.correlation_id)
        if self.failure_reason is not None:
            normalized = self.failure_reason.strip()
            self.failure_reason = normalized or None

    @classmethod
    def create(
        cls,
        *,
        payment_id: PaymentId | UUID | None = None,
        order_id: UUID,
        user_id: str,
        amount: Money | Decimal,
        currency: str = "USD",
        correlation_id: str = "",
    ) -> "Payment":
        return cls(
            payment_id=payment_id or PaymentId.new(),
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=PaymentStatusState.pending(),
            correlation_id=correlation_id,
        )

    def transition_to(self, next_status: PaymentStatusState | str) -> None:
        self.status = self.status.transition_to(next_status)

    def succeed(self) -> None:
        self.transition_to(PaymentStatusState.success())
        self.failure_reason = None

    def fail(self, reason: str | None = None) -> None:
        self.transition_to(PaymentStatusState.failed())
        self.failure_reason = (reason or "Payment failed").strip() or "Payment failed"

    def refund(self) -> None:
        self.transition_to(PaymentStatusState.refunded())


PaymentEntity = Payment
