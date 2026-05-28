"""Shared safe application exceptions."""

from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, status


@dataclass(slots=True)
class AppError(Exception):
    message: str
    error_code: str = "APP_ERROR"
    status_code: int = status.HTTP_400_BAD_REQUEST
    details: dict[str, Any] = field(default_factory=dict)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", **details: Any) -> None:
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict", **details: Any) -> None:
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", **details: Any) -> None:
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", **details: Any) -> None:
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


def to_http_exception(error: AppError) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={
            "error_code": error.error_code,
            "message": error.message,
            "details": error.details,
        },
    )
