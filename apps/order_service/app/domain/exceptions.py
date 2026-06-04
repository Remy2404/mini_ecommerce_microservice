class CartNotFoundError(Exception):
    """Raised when an order is created for a missing cart."""


class EmptyCartError(Exception):
    """Raised when an order is created from an empty cart."""


class InvalidStateTransitionException(Exception):
    """Raised when an order cannot move to the requested state."""

