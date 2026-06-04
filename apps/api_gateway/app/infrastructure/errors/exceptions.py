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
