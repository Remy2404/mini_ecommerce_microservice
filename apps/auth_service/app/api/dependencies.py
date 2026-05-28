"""Auth Service request dependencies."""

from fastapi import Header, HTTPException, status

from packages.security.jwt_validator import (
    AuthProviderUnavailableError,
    TokenValidationError,
    validate_wso2_access_token,
)


async def get_current_token_payload(
    authorization: str | None = Header(default=None),
) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        return await validate_wso2_access_token(token)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    except AuthProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc
