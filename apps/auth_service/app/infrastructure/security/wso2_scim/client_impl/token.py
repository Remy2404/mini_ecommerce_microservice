from __future__ import annotations

from http import HTTPStatus

import httpx

from apps.auth_service.app.infrastructure.config.settings import settings

from ..errors import WSO2SCIMError
from .transport import _log_wso2_event, _safe_wso2_error_code, _service_basic_auth


async def _service_access_token(
    client: httpx.AsyncClient,
    *,
    scope: str,
    request_id: str | None = None,
) -> str:
    target_url = settings.wso2_token_url
    try:
        response = await client.post(
            target_url,
            data={
                "grant_type": "client_credentials",
                "scope": scope,
            },
            auth=_service_basic_auth(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    except httpx.HTTPError as exc:
        _log_wso2_event(
            "error",
            "WSO2 client_credentials token request was unavailable",
            request_id=request_id,
            target_url=target_url,
            error_type=exc.__class__.__name__,
        )
        raise WSO2SCIMError(
            "Authentication service unavailable",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type=exc.__class__.__name__,
            target_url=target_url,
        ) from exc
    if response.status_code >= 400:
        wso2_error_code = _safe_wso2_error_code(response)
        _log_wso2_event(
            "error",
            "WSO2 client_credentials token request failed",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="client_credentials_failed",
            wso2_error_code=wso2_error_code,
        )
        raise WSO2SCIMError(
            "WSO2 registration configuration error",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type="client_credentials_failed",
            target_url=target_url,
            wso2_error_code=wso2_error_code,
        )

    try:
        token = response.json().get("access_token")
    except ValueError as exc:
        _log_wso2_event(
            "error",
            "WSO2 token response was not valid JSON",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="invalid_json",
        )
        raise WSO2SCIMError(
            "WSO2 registration configuration error",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type="invalid_json",
            target_url=target_url,
        ) from exc

    if not token:
        _log_wso2_event(
            "error",
            "WSO2 token response did not include an access token",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="missing_access_token",
        )
        raise WSO2SCIMError(
            "WSO2 registration configuration error",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type="missing_access_token",
            target_url=target_url,
        )
    return str(token)


async def _service_request_headers(
    client: httpx.AsyncClient,
    *,
    scope: str,
    request_id: str | None = None,
) -> dict[str, str]:
    access_token = await _service_access_token(
        client,
        scope=scope,
        request_id=request_id,
    )
    return {"Authorization": f"Bearer {access_token}"}
