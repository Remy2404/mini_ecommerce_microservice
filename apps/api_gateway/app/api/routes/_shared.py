import json
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from apps.api_gateway.app.api.dependencies import rate_limit, validate_token
from apps.api_gateway.app.infrastructure.config.settings import settings
from apps.api_gateway.app.infrastructure.errors.exceptions import ForbiddenError
from apps.api_gateway.app.infrastructure.security.headers import (
    AUTHENTICATED_USER_ID_HEADER,
)
from apps.api_gateway.app.infrastructure.security.permissions import (
    require_owner_or_role,
)


def current_user_id(payload: dict) -> str:
    user_id = str(payload.get("sub") or "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return user_id


def owner_headers(payload: dict) -> dict[str, str]:
    return {AUTHENTICATED_USER_ID_HEADER: current_user_id(payload)}


async def json_body(request: Request) -> dict[str, Any]:
    raw_body = await request.body()
    if not raw_body:
        return {}

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Invalid JSON body") from exc

    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="Request body must be an object")
    return body


async def owned_body(request: Request) -> bytes:
    body = await json_body(request)
    if "user_id" in body:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return json.dumps(body, separators=(",", ":")).encode("utf-8")


async def enforce_gateway_access(
    request: Request,
    payload: dict = Depends(validate_token),
) -> dict:
    await rate_limit(request, payload)
    return payload


def enforce_user_scope(payload: dict, resource_user_id: str) -> None:
    if not settings.gateway_auth_enabled:
        return

    try:
        require_owner_or_role(
            resource_owner_id=resource_user_id,
            current_user_id=str(payload.get("sub", "")),
            user_roles=payload.get("roles", []),
            role="admin",
        )
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        ) from exc
