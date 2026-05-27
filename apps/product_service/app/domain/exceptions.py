"""Product Service domain exceptions."""


class CategoryAlreadyExistsError(Exception):
    """Raised when a category name already exists."""


class CategoryNotFoundError(Exception):
    """Raised when a category does not exist."""


class ProductNotFoundError(Exception):
    """Raised when a product does not exist."""
