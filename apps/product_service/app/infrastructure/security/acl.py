"""Product Service anti-corruption layer for external auth checks."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from apps.product_service.app.infrastructure.errors.exceptions import to_http_exception
from apps.product_service.app.infrastructure.security import jwt_validator
from apps.product_service.app.infrastructure.security.jwt_validator import (
    TokenValidationError,
)
from apps.product_service.app.infrastructure.security.permissions import require_scope


async def require_product_image_write_scope(
    authorization: str | None = Header(None),
) -> None:
    """Validate the forwarded WSO2 token and require the image-write scope."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization",
        )

    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization.split(None, 1)[1]
    try:
        payload = await jwt_validator.validate_wso2_access_token(token)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth provider unavailable",
        ) from exc

    try:
        require_scope(payload.get("scope", ""), "product_image_write")
    except Exception as exc:
        raise to_http_exception(exc) from exc
