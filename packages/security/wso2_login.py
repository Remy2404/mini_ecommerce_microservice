"""WSO2 password-grant login helpers."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException, status

from packages.config.settings import settings
from packages.observability.logging import get_logger
from packages.security.oauth_errors import (
    is_client_configuration_error,
    oauth_error_code,
)


logger = get_logger(__name__)


async def request_wso2_password_token(
    *,
    username: str,
    password: str,
    scope: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    target_url = settings.wso2_token_url
    token_request = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": scope,
        "client_id": settings.wso2_client_id,
        "client_secret": settings.wso2_client_secret,
    }

    try:
        async with httpx.AsyncClient(
            timeout=settings.wso2_request_timeout_seconds,
            verify=settings.wso2_verify_ssl,
        ) as client:
            response = await client.post(
                target_url,
                data=token_request,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.HTTPError as exc:
        logger.error(
            "WSO2 password token request was unavailable",
            request_id=request_id,
            target_url=target_url,
            error_type=exc.__class__.__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc

    error_code = oauth_error_code(response)

    if error_code == "invalid_grant":
        logger.warning(
            "WSO2 rejected password grant",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="invalid_grant",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if is_client_configuration_error(error_code):
        logger.error(
            "WSO2 token request rejected due to client configuration",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type=error_code or "client_configuration_error",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    if response.status_code >= 500:
        logger.error(
            "WSO2 token endpoint returned an error",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="server_error",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    if response.status_code >= 400:
        logger.error(
            "WSO2 token endpoint returned a client error",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type=error_code or "client_error",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    return response.json()
