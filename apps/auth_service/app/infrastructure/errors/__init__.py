"""Auth Service safe application errors."""

from apps.auth_service.app.infrastructure.errors.exceptions import (
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
