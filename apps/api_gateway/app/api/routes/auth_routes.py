from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, status

from apps.api_gateway.app.schemas.requests import WSO2PasswordLoginRequest
from packages.config.settings import settings

router = APIRouter()


@router.post(
    "/auth/login",
    tags=["WSO2 Auth"],
    summary="Login to WSO2 with username and password",
    description=(
        "Returns WSO2 tokens for local Swagger testing. Copy the returned "
        "access_token into Swagger Authorize as the bearer token; do not use "
        "the id_token for API gateway requests."
    ),
)
async def wso2_login(request: WSO2PasswordLoginRequest) -> dict[str, Any]:
    token_request = {
        "grant_type": "password",
        "username": request.username,
        "password": request.password.get_secret_value(),
        "scope": request.scope,
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

    if response.status_code in {400, 401, 403}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
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
