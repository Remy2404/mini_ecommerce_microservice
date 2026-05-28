"""Payment Service policy checks."""

from decimal import Decimal


def ensure_payable_amount(amount: Decimal) -> None:
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero")
