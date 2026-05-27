class CartNotFoundError(Exception):
    """Raised when an order is created for a missing cart."""


class EmptyCartError(Exception):
    """Raised when an order is created from an empty cart."""
