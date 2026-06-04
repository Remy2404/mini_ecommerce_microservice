from typing import Any

from fastapi import APIRouter

from apps.api_gateway.app.infrastructure.security.wso2_login import (
    request_wso2_password_token,
)
from apps.api_gateway.app.schemas.requests import WSO2PasswordLoginRequest
from apps.api_gateway.app.schemas.responses import DetailErrorResponse, WSO2TokenResponse

router = APIRouter(prefix="/auth")


@router.post(
    "/login",
    tags=["WSO2 Gateway"],
    response_model=WSO2TokenResponse,
    summary="Login via WSO2 Identity Server",
    description=(
        "Authenticates a WSO2 Identity Server user and returns the WSO2 token "
        "response. Use the WSO2 username from registration. Copy the full WSO2 "
        "invitation password exactly, including trailing symbols."
    ),
    responses={
        401: {
            "model": DetailErrorResponse,
            "description": "Invalid username or password.",
        },
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 is unavailable or the gateway WSO2 client is misconfigured.",
        },
    },
)
async def login_user(request: WSO2PasswordLoginRequest) -> dict[str, Any]:
    return await request_wso2_password_token(
        username=request.username,
        password=request.password.get_secret_value(),
        scope=request.scope,
    )
