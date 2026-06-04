"""WSO2 SCIM2 user management helpers."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import httpx

from apps.auth_service.app.infrastructure.config.settings import settings

from .client import (
    _log_wso2_event,
    _raise_scim_error,
    _scim_url,
    _service_request_headers,
)
from .current_user import (
    _current_wso2_user,
    _get_wso2_userinfo,
)
from .errors import WSO2SCIMError
from .mappers import (
    _escape_scim_filter_value,
    _normalize_scim_user,
    _register_user_response,
    _scim_create_user_payload,
)


async def register_wso2_user(
    *,
    username: str,
    email: str,
    password: str,
    given_name: str,
    family_name: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    return await _register_wso2_user(
        username=username,
        email=email,
        password=password,
        given_name=given_name,
        family_name=family_name,
        request_id=request_id,
    )


async def _register_wso2_user(
    *,
    username: str,
    email: str,
    password: str,
    given_name: str,
    family_name: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    user_create_url = _scim_url("Users")
    async with httpx.AsyncClient(
        timeout=settings.wso2_request_timeout_seconds,
        verify=settings.wso2_verify_ssl,
    ) as client:
        headers = await _service_request_headers(
            client,
            scope=settings.wso2_scim_create_scope,
            request_id=request_id,
        )
        try:
            response = await client.post(
                user_create_url,
                json=_scim_create_user_payload(
                    username=username,
                    email=email,
                    password=password,
                    given_name=given_name,
                    family_name=family_name,
                ),
                headers={
                    **headers,
                    "Accept": "application/scim+json",
                    "Content-Type": "application/scim+json",
                },
            )
        except httpx.HTTPError as exc:
            _log_wso2_event(
                "error",
                "WSO2 SCIM user create endpoint was unavailable",
                request_id=request_id,
                target_url=user_create_url,
                error_type=exc.__class__.__name__,
            )
            raise WSO2SCIMError(
                "Authentication service unavailable",
                status_code=502,
                error_type=exc.__class__.__name__,
                target_url=user_create_url,
            ) from exc

        if response.status_code >= 400:
            raise _raise_scim_error(
                operation="registration",
                response=response,
                request_id=request_id,
                target_url=user_create_url,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            _log_wso2_event(
                "error",
                "WSO2 user registration returned invalid JSON",
                request_id=request_id,
                target_url=user_create_url,
                status_code=response.status_code,
                error_type="invalid_json",
            )
            raise WSO2SCIMError(
                "Authentication service unavailable",
                status_code=502,
                error_type="invalid_json",
                target_url=user_create_url,
            ) from exc

    return _register_user_response(
        payload,
        fallback_username=username,
        fallback_email=email,
    )


async def get_wso2_user_by_id(
    user_id: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    return await _get_wso2_user_by_id(user_id, request_id=request_id)


async def _get_wso2_user_by_id(
    user_id: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Fetch a single WSO2 user by SCIM2 id and return a normalized dict."""
    target_url = _scim_url(f"Users/{user_id}")
    async with httpx.AsyncClient(
        timeout=settings.wso2_request_timeout_seconds,
        verify=settings.wso2_verify_ssl,
    ) as client:
        headers = await _service_request_headers(
            client,
            scope=settings.wso2_scim_view_scope,
            request_id=request_id,
        )
        try:
            response = await client.get(
                target_url,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            _log_wso2_event(
                "error",
                "WSO2 SCIM user lookup was unavailable",
                request_id=request_id,
                target_url=target_url,
                error_type=exc.__class__.__name__,
            )
            raise WSO2SCIMError(
                "Authentication service unavailable",
                status_code=502,
                error_type=exc.__class__.__name__,
                target_url=target_url,
            ) from exc

    if response.status_code >= 400:
        raise _raise_scim_error(
            operation="lookup",
            response=response,
            request_id=request_id,
            target_url=target_url,
        )

    try:
        payload = response.json()
    except ValueError as exc:
        _log_wso2_event(
            "error",
            "WSO2 SCIM user lookup returned invalid JSON",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="invalid_json",
        )
        raise WSO2SCIMError(
            "Authentication service unavailable",
            status_code=502,
            error_type="invalid_json",
            target_url=target_url,
        ) from exc

    normalized = _normalize_scim_user(payload)
    return {"user": normalized}


async def filter_wso2_users(
    *,
    filter_query: str | None = None,
    attributes: str | None = None,
    excluded_attributes: str | None = None,
    start_index: int = 1,
    count: int = 25,
    domain: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    return await _filter_wso2_users(
        filter_query=filter_query,
        attributes=attributes,
        excluded_attributes=excluded_attributes,
        start_index=start_index,
        count=count,
        domain=domain,
        request_id=request_id,
    )


async def _filter_wso2_users(
    *,
    filter_query: str | None = None,
    attributes: str | None = None,
    excluded_attributes: str | None = None,
    start_index: int = 1,
    count: int = 25,
    domain: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Query WSO2 SCIM2 GET /scim2/Users with optional filter/pagination."""
    target_url = _scim_url("Users")

    params: dict[str, str | int] = {
        "startIndex": start_index,
        "count": count,
    }
    if filter_query:
        params["filter"] = filter_query
    if attributes:
        params["attributes"] = attributes
    if excluded_attributes:
        params["excludedAttributes"] = excluded_attributes
    if domain:
        params["domain"] = domain

    async with httpx.AsyncClient(
        timeout=settings.wso2_request_timeout_seconds,
        verify=settings.wso2_verify_ssl,
    ) as client:
        headers = await _service_request_headers(
            client,
            scope=settings.wso2_scim_list_scope,
            request_id=request_id,
        )
        try:
            response = await client.get(
                target_url,
                params=params,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            _log_wso2_event(
                "error",
                "WSO2 SCIM user list endpoint was unavailable",
                request_id=request_id,
                target_url=target_url,
                error_type=exc.__class__.__name__,
            )
            raise WSO2SCIMError(
                "Authentication service unavailable",
                status_code=502,
                error_type=exc.__class__.__name__,
                target_url=target_url,
            ) from exc

    if response.status_code >= 400:
        raise _raise_scim_error(
            operation="list",
            response=response,
            request_id=request_id,
            target_url=target_url,
        )

    try:
        payload = response.json()
    except ValueError as exc:
        _log_wso2_event(
            "error",
            "WSO2 SCIM user list returned invalid JSON",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="invalid_json",
        )
        raise WSO2SCIMError(
            "Authentication service unavailable",
            status_code=502,
            error_type="invalid_json",
            target_url=target_url,
        ) from exc

    resources = payload.get("Resources") or []
    if not isinstance(resources, list):
        resources = []
    users = [_normalize_scim_user(r) for r in resources if isinstance(r, dict)]

    return {
        "total_results": int(payload.get("totalResults", 0)),
        "start_index": int(payload.get("startIndex", 1)),
        "items_per_page": int(payload.get("itemsPerPage", len(users))),
        "users": users,
    }


async def search_wso2_users(
    *,
    query: str,
    start_index: int = 1,
    count: int = 25,
    request_id: str | None = None,
    filter_func: Callable[..., Awaitable[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    return await _search_wso2_users(
        query=query,
        start_index=start_index,
        count=count,
        request_id=request_id,
        filter_func=filter_func or filter_wso2_users,
    )


async def _search_wso2_users(
    *,
    query: str,
    start_index: int = 1,
    count: int = 25,
    request_id: str | None = None,
    filter_func: Callable[..., Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    """Build a safe SCIM filter from a keyword and delegate to filter_wso2_users."""
    escaped = _escape_scim_filter_value(query)
    scim_filter = f'userName co "{escaped}" or emails co "{escaped}"'
    return await filter_func(
        filter_query=scim_filter,
        start_index=start_index,
        count=count,
        request_id=request_id,
    )


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


__all__ = [
    "WSO2SCIMError",
    "current_wso2_user",
    "filter_wso2_users",
    "get_wso2_user_by_id",
    "get_wso2_userinfo",
    "httpx",
    "register_wso2_user",
    "search_wso2_users",
]
