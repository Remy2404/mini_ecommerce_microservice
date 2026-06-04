from __future__ import annotations

from http import HTTPStatus

import httpx

from apps.auth_service.app.infrastructure.config.settings import settings
from apps.auth_service.app.infrastructure.observability.logging import get_logger

from ..errors import WSO2SCIMError


logger = get_logger(__name__)


def _scim_url(path: str) -> str:
    return f"{settings.wso2_base_url.rstrip('/')}/scim2/{path.lstrip('/')}"


def _log_wso2_event(
    level: str,
    message: str,
    *,
    request_id: str | None,
    target_url: str,
    status_code: int | None = None,
    error_type: str | None = None,
    wso2_error_code: str | None = None,
) -> None:
    log_method = getattr(logger, level, logger.info)
    log_method(
        message,
        request_id=request_id,
        target_url=target_url,
        status_code=status_code,
        error_type=error_type,
        wso2_error_code=wso2_error_code,
    )


def _safe_wso2_error_code(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None

    if not isinstance(payload, dict):
        return None

    for key in ("scimType", "error", "code", "status"):
        value = payload.get(key)
        if isinstance(value, str | int):
            return str(value)

    return None


def _service_basic_auth() -> tuple[str, str]:
    return settings.wso2_client_id, settings.wso2_client_secret


def _raise_scim_error(
    *,
    operation: str,
    response: httpx.Response,
    request_id: str | None,
    target_url: str,
) -> WSO2SCIMError:
    upstream_status_code = response.status_code
    status_code = upstream_status_code
    error_type = f"scim_{operation}_failed"
    message = "Authentication service unavailable"
    wso2_error_code = _safe_wso2_error_code(response)

    if upstream_status_code == HTTPStatus.BAD_REQUEST:
        message = (
            "Invalid registration request"
            if operation == "registration"
            else "Invalid WSO2 SCIM request"
        )
        error_type = f"scim_{operation}_bad_request"
    elif upstream_status_code == HTTPStatus.NOT_FOUND:
        message = "User not found"
        status_code = HTTPStatus.NOT_FOUND
        error_type = f"scim_{operation}_not_found"
    elif upstream_status_code == HTTPStatus.CONFLICT:
        message = "User already exists"
        error_type = f"scim_{operation}_conflict"
    elif upstream_status_code == HTTPStatus.UNAUTHORIZED:
        status_code = HTTPStatus.BAD_GATEWAY
        message = "WSO2 service credential error"
        error_type = f"scim_{operation}_credential_error"
    elif upstream_status_code == HTTPStatus.FORBIDDEN:
        status_code = HTTPStatus.FORBIDDEN
        message = "Insufficient WSO2 scope for this operation"
        error_type = f"scim_{operation}_forbidden"
    else:
        status_code = HTTPStatus.BAD_GATEWAY

    _log_wso2_event(
        "error",
        f"WSO2 {operation.replace('_', ' ')} failed",
        request_id=request_id,
        target_url=target_url,
        status_code=upstream_status_code,
        error_type=error_type,
        wso2_error_code=wso2_error_code,
    )
    return WSO2SCIMError(
        message,
        status_code=status_code,
        error_type=error_type,
        target_url=target_url,
        wso2_error_code=wso2_error_code,
    )
