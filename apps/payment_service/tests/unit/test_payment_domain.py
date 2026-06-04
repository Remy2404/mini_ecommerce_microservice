from decimal import Decimal
from uuid import uuid4

import pytest

from apps.payment_service.app.domain.entities import Payment
from apps.payment_service.app.domain.exceptions import (
    InvalidPaymentStateTransitionException,
)
from apps.payment_service.app.domain.value_objects import Money, PaymentStatusState


def test_payment_rejects_invalid_amount() -> None:
    with pytest.raises(ValueError, match="Payment amount must be greater than zero"):
        Payment.create(
            order_id=uuid4(),
            user_id="user_123",
            amount=Money(Decimal("0.00")),
        )


def test_payment_state_machine_accepts_valid_transitions() -> None:
    payment = Payment.create(
        order_id=uuid4(),
        user_id="user_123",
        amount=Money(Decimal("10.00")),
    )

    payment.succeed()
    assert payment.status == PaymentStatusState.success()
    assert payment.failure_reason is None

    payment.refund()
    assert payment.status == PaymentStatusState.refunded()


def test_payment_state_machine_rejects_invalid_transition() -> None:
    payment = Payment.create(
        order_id=uuid4(),
        user_id="user_123",
        amount=Money(Decimal("10.00")),
    )
    payment.fail("declined")

    with pytest.raises(InvalidPaymentStateTransitionException, match="Cannot transition payment from FAILED"):
        payment.refund()
