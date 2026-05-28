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
) -> dict[str, Any]:
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
                settings.wso2_token_url,
                data=token_request,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc

    error_code = oauth_error_code(response)

    if error_code == "invalid_grant":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if is_client_configuration_error(error_code):
        logger.error(
            "WSO2 token request rejected due to gateway client configuration",
            error_code=error_code,
            status_code=response.status_code,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Authentication service error",
        )

    return response.json()
