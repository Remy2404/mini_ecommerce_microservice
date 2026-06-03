from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status

from apps.api_gateway.app.api.routes._shared import enforce_gateway_access
from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request
from apps.api_gateway.app.infrastructure.security.wso2_login import (
    request_wso2_password_token,
)
from apps.api_gateway.app.schemas.requests import (
    GatewayRegisterUserRequest,
    WSO2PasswordLoginRequest,
    swagger_request_body,
)
from apps.api_gateway.app.schemas.responses import (
    DetailErrorResponse,
    GatewayRegisterUserResponse,
    GatewayWso2UserDetailResponse,
    GatewayWso2UsersListResponse,
    WSO2TokenResponse,
)

router = APIRouter(prefix="/auth")


@router.post(
    "/register",
    tags=["WSO2 Gateway"],
    status_code=status.HTTP_201_CREATED,
    response_model=GatewayRegisterUserResponse,
    summary="Register user in WSO2 Identity Server",
    description=(
        "Creates a WSO2 Identity Server user through SCIM2. WSO2 client "
        "credentials stay behind the backend."
    ),
    responses={
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 is unavailable or registration is not configured.",
        },
    },
    openapi_extra=swagger_request_body(GatewayRegisterUserRequest),
)
async def register_user(
    request: Request,
):
    return await forward_request("auth", "register", request)


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


@router.get(
    "/users",
    tags=["WSO2 Gateway"],
    response_model=GatewayWso2UsersListResponse,
    summary="List or filter WSO2 users",
    description=(
        "Proxies to Auth Service WSO2 SCIM2 user listing. Requires a gateway "
        "bearer token when gateway auth is enabled."
    ),
    responses={
        401: {"model": DetailErrorResponse, "description": "Missing or invalid token."},
        403: {"model": DetailErrorResponse, "description": "Insufficient WSO2 scope."},
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 or Auth Service is unavailable.",
        },
    },
)
async def list_wso2_users(
    request: Request,
    filter_: str | None = Query(
        default=None,
        alias="filter",
        description="SCIM2 filter expression.",
    ),
    attributes: str | None = Query(
        default=None,
        description="Comma-separated attributes to include.",
    ),
    excluded_attributes: str | None = Query(
        default=None,
        alias="excludedAttributes",
        description="Comma-separated attributes to exclude.",
    ),
    start_index: int = Query(default=1, ge=1, alias="startIndex"),
    count: int = Query(default=25, ge=1, le=100),
    domain: str | None = Query(default=None, description="WSO2 user store domain."),
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", "users", request)


@router.get(
    "/users/search",
    tags=["WSO2 Gateway"],
    response_model=GatewayWso2UsersListResponse,
    summary="Search WSO2 users",
    description=(
        "Proxies to Auth Service WSO2 user search, which builds a safe SCIM2 "
        "filter from the keyword."
    ),
    responses={
        401: {"model": DetailErrorResponse, "description": "Missing or invalid token."},
        403: {"model": DetailErrorResponse, "description": "Insufficient WSO2 scope."},
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 or Auth Service is unavailable.",
        },
    },
)
async def search_wso2_users(
    request: Request,
    q: str = Query(min_length=1, max_length=255, description="Search term."),
    start_index: int = Query(default=1, ge=1, alias="startIndex"),
    count: int = Query(default=25, ge=1, le=100),
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", "users/search", request)


@router.get(
    "/users/{user_id}",
    tags=["WSO2 Gateway"],
    response_model=GatewayWso2UserDetailResponse,
    summary="Get WSO2 user by SCIM ID",
    description="Proxies to Auth Service WSO2 SCIM2 user detail lookup.",
    responses={
        401: {"model": DetailErrorResponse, "description": "Missing or invalid token."},
        403: {"model": DetailErrorResponse, "description": "Insufficient WSO2 scope."},
        404: {"model": DetailErrorResponse, "description": "User not found."},
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 or Auth Service is unavailable.",
        },
    },
)
async def get_wso2_user(
    user_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", f"users/{user_id}", request)
