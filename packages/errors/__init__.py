"""Safe application errors and FastAPI handlers."""

from packages.errors.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    to_http_exception,
)

__all__ = [
    "AppError",
    "ConflictError",
    "ForbiddenError",
    "NotFoundError",
    "UnauthorizedError",
    "to_http_exception",
]
