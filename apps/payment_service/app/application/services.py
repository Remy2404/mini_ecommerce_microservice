"""Payment Service business logic."""

from dataclasses import dataclass
from decimal import Decimal

from apps.payment_service.app.domain.policies import ensure_payable_amount
from apps.payment_service.app.infrastructure.config.settings import settings


@dataclass(frozen=True)
class PaymentDecision:
    succeeded: bool
    failure_reason: str | None = None


def process_fake_payment(*, amount: Decimal, random_value: float) -> PaymentDecision:
    try:
        ensure_payable_amount(amount)
    except ValueError as exc:
        return PaymentDecision(False, str(exc))

    if random_value <= settings.payment_success_rate:
        return PaymentDecision(True)

    return PaymentDecision(False, "Simulated payment failure")

