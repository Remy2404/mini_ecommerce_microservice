from __future__ import annotations

from typing import Any

from apps.auth_service.app.infrastructure.config.settings import settings

from . import httpx
from .client import (
    _log_wso2_event,
    _raise_scim_error,
    _scim_url,
    _service_request_headers,
)
from .errors import WSO2SCIMError
from .mappers import _register_user_response, _scim_create_user_payload


async def register_wso2_user(
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
