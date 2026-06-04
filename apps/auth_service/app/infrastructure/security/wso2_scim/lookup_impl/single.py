from __future__ import annotations

from typing import Any

import httpx

from apps.auth_service.app.infrastructure.config.settings import settings

from ..client import _log_wso2_event, _raise_scim_error, _scim_url, _service_request_headers
from ..errors import WSO2SCIMError
from ..mappers import _normalize_scim_user


async def get_wso2_user_by_id(
    user_id: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
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
