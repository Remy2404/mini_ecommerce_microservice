"""JWT issuing and validation helpers."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from packages.config.settings import settings
from packages.errors.exceptions import UnauthorizedError


def _jwt_secret() -> str:
    secret = settings.jwt_secret_key.get_secret_value()
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY must be configured to issue local JWTs")
    return secret


def create_access_token(
    *,
    subject: str,
    roles: list[str] | None = None,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    expires_at = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "roles": roles or [],
        "iat": datetime.now(UTC),
        "exp": expires_at,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid token") from exc

    if payload.get("type") != "access" or not payload.get("sub"):
        raise UnauthorizedError("Invalid token")

    return payload
