"""Payment Service business logic."""

from dataclasses import dataclass
from decimal import Decimal

from packages.config.settings import settings


@dataclass(frozen=True)
class PaymentDecision:
    succeeded: bool
    failure_reason: str | None = None


def process_fake_payment(*, amount: Decimal, random_value: float) -> PaymentDecision:
    if amount <= 0:
        return PaymentDecision(False, "Invalid payment amount")

    if random_value <= settings.payment_success_rate:
        return PaymentDecision(True)

    return PaymentDecision(False, "Simulated payment failure")
