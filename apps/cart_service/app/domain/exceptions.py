class ProductNotFoundError(Exception):
    """Raised when the requested product does not exist."""


class ProductLookupRejectedError(Exception):
    """Raised when Product Service rejects a product lookup."""


class ProductServiceUnavailableError(Exception):
    """Raised when trusted product data cannot be fetched safely."""
