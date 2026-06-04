from __future__ import annotations

from http import HTTPStatus
from typing import Any, Awaitable, Callable

from apps.auth_service.app.infrastructure.config.settings import settings

from . import httpx
from .client import _log_wso2_event, _safe_wso2_error_code
from .errors import WSO2SCIMError
from .mappers import _claim_user_response, _roles_from_token
from .lookup import get_wso2_user_by_id


async def _get_wso2_userinfo(
    access_token: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any] | None:
    target_url = settings.wso2_userinfo_url
    try:
        async with httpx.AsyncClient(
            timeout=settings.wso2_request_timeout_seconds,
            verify=settings.wso2_verify_ssl,
        ) as client:
            response = await client.get(
                target_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
    except httpx.HTTPError as exc:
        _log_wso2_event(
            "warning",
            "WSO2 userinfo endpoint was unavailable; falling back to SCIM lookup",
            request_id=request_id,
            target_url=target_url,
            error_type=exc.__class__.__name__,
        )
        return None

    if response.status_code >= 400:
        _log_wso2_event(
            "warning",
            "WSO2 userinfo endpoint returned an error; falling back to SCIM lookup",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="userinfo_failed",
            wso2_error_code=_safe_wso2_error_code(response),
        )
        return None

    try:
        payload = response.json()
    except ValueError:
        _log_wso2_event(
            "warning",
            "WSO2 userinfo endpoint returned invalid JSON; falling back to SCIM lookup",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="invalid_json",
        )
        return None

    return payload if isinstance(payload, dict) else None


async def _current_wso2_user(
    token_payload: dict[str, Any],
    *,
    access_token: str | None = None,
    request_id: str | None = None,
    get_wso2_userinfo_func: Callable[..., Awaitable[dict[str, Any] | None]],
    get_wso2_user_by_id_func: Callable[..., Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    if token_payload.get("aut") != "APPLICATION_USER":
        raise WSO2SCIMError(
            "User token required",
            status_code=HTTPStatus.FORBIDDEN,
            error_type="user_token_required",
        )

    user_id = str(token_payload.get("sub") or "")
    if not user_id:
        raise WSO2SCIMError("Token payload has no subject")

    roles = _roles_from_token(token_payload)
    claim_response = _claim_user_response(token_payload, user_id=user_id, roles=roles)
    if claim_response is not None:
        return claim_response

    if access_token:
        userinfo = await get_wso2_userinfo_func(access_token, request_id=request_id)
        if userinfo is not None:
            claim_response = _claim_user_response(
                userinfo,
                user_id=str(userinfo.get("sub") or user_id),
                roles=roles,
            )
            if claim_response is not None:
                return claim_response

    detail = await get_wso2_user_by_id_func(user_id, request_id=request_id)
    user = detail["user"]
    return {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "roles": user["roles"],
    }


async def get_wso2_userinfo(
    access_token: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any] | None:
    return await _get_wso2_userinfo(access_token, request_id=request_id)


async def current_wso2_user(
    token_payload: dict[str, Any],
    *,
    access_token: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    return await _current_wso2_user(
        token_payload,
        access_token=access_token,
        request_id=request_id,
        get_wso2_userinfo_func=get_wso2_userinfo,
        get_wso2_user_by_id_func=get_wso2_user_by_id,
    )
