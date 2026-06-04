from __future__ import annotations

from typing import Any

import httpx

from apps.auth_service.app.infrastructure.config.settings import settings

from ..client import _log_wso2_event, _raise_scim_error, _scim_url, _service_request_headers
from ..errors import WSO2SCIMError
from ..mappers import _normalize_scim_user


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
