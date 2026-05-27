"""Payment Service domain exceptions."""


class DuplicatePaymentEventError(Exception):
    """Raised when a payment event was already processed."""


class PaymentNotFoundError(Exception):
    """Raised when a payment row does not exist."""
