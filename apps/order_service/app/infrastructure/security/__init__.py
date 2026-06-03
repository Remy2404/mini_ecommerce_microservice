"""Order Service security helpers."""

from apps.order_service.app.infrastructure.security.headers import (
    AUTHENTICATED_USER_ID_HEADER,
)

__all__ = ["AUTHENTICATED_USER_ID_HEADER"]
