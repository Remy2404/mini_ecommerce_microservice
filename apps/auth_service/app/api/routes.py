"""Auth Service routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from apps.auth_service.app.application.services import AuthService, get_auth_service
from apps.auth_service.app.schemas.requests import RegisterUserRequest
from apps.auth_service.app.schemas.responses import (
    RegisterUserResponse,
    Wso2UserDetailResponse,
    Wso2UsersListResponse,
)
from apps.api_gateway.app.schemas.requests import WSO2PasswordLoginRequest
from packages.config.settings import settings
from packages.contracts.common.schemas import ApiResponse
from packages.observability.logging import get_logger
from packages.security.wso2_login import request_wso2_password_token
from packages.security.wso2_scim import (
    WSO2SCIMError,
    filter_wso2_users,
    get_wso2_user_by_id,
    search_wso2_users,
)

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.auth_service_name}


@router.post(
    "/auth/register",
    response_model=ApiResponse[RegisterUserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register user with WSO2",
    description="Creates a new user in WSO2 Identity Server using SCIM2.",
)
async def register_user(
    request: Request,
    payload: RegisterUserRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[RegisterUserResponse]:
    request_id = request.headers.get("x-request-id")
    try:
        user = await service.register_user(payload, request_id=request_id)
    except WSO2SCIMError as exc:
        logger.error(
            "WSO2 user registration failed",
            request_id=request_id,
            target_url=exc.target_url,
            status_code=exc.status_code,
            error_type=exc.error_type,
            wso2_error_code=exc.wso2_error_code,
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return ApiResponse(
        success=True,
        message="User registered successfully",
        data=user,
    )


# ---------------------------------------------------------------------------
# WSO2 SCIM2 user query routes
# ---------------------------------------------------------------------------


@router.get(
    "/auth/users",
    response_model=ApiResponse[Wso2UsersListResponse],
    summary="Filter/list users from WSO2",
    description="Proxies to WSO2 SCIM2 GET /scim2/Users. Scope: internal_user_mgt_list.",
)
async def list_users(
    request: Request,
    filter_: str | None = Query(
        default=None,
        alias="filter",
        description="SCIM2 filter expression",
    ),
    attributes: str | None = Query(
        default=None,
        description="Comma-separated attributes to include",
    ),
    excluded_attributes: str | None = Query(
        default=None,
        alias="excludedAttributes",
        description="Comma-separated attributes to exclude",
    ),
    start_index: int = Query(default=1, ge=1, alias="startIndex"),
    count: int = Query(default=25, ge=1, le=100),
    domain: str | None = Query(default=None, description="WSO2 user store domain"),
) -> ApiResponse[Wso2UsersListResponse]:
    request_id = request.headers.get("x-request-id")
    try:
        result = await filter_wso2_users(
            filter_query=filter_,
            attributes=attributes,
            excluded_attributes=excluded_attributes,
            start_index=start_index,
            count=count,
            domain=domain,
            request_id=request_id,
        )
    except WSO2SCIMError as exc:
        logger.error(
            "WSO2 user list failed",
            request_id=request_id,
            target_url=exc.target_url,
            status_code=exc.status_code,
            error_type=exc.error_type,
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return ApiResponse(
        success=True,
        message="Users retrieved successfully",
        data=Wso2UsersListResponse(**result),
    )


@router.get(
    "/auth/users/search",
    response_model=ApiResponse[Wso2UsersListResponse],
    summary="Search users by keyword",
    description="Safe search wrapper that builds a SCIM2 filter from a keyword. Scope: internal_user_mgt_list.",
)
async def search_users_route(
    request: Request,
    q: str = Query(min_length=1, max_length=255, description="Search term"),
    start_index: int = Query(default=1, ge=1, alias="startIndex"),
    count: int = Query(default=25, ge=1, le=100),
) -> ApiResponse[Wso2UsersListResponse]:
    request_id = request.headers.get("x-request-id")
    try:
        result = await search_wso2_users(
            query=q,
            start_index=start_index,
            count=count,
            request_id=request_id,
        )
    except WSO2SCIMError as exc:
        logger.error(
            "WSO2 user search failed",
            request_id=request_id,
            target_url=exc.target_url,
            status_code=exc.status_code,
            error_type=exc.error_type,
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return ApiResponse(
        success=True,
        message="Search results retrieved successfully",
        data=Wso2UsersListResponse(**result),
    )


@router.get(
    "/auth/users/{user_id}",
    response_model=ApiResponse[Wso2UserDetailResponse],
    summary="Get user by WSO2 SCIM ID",
    description="Fetches a single user from WSO2 by SCIM2 user ID. Scope: internal_user_mgt_view.",
)
async def get_user_by_id_route(
    request: Request,
    user_id: str,
) -> ApiResponse[Wso2UserDetailResponse]:
    request_id = request.headers.get("x-request-id")
    try:
        user = await get_wso2_user_by_id(user_id, request_id=request_id)
    except WSO2SCIMError as exc:
        logger.error(
            "WSO2 user lookup failed",
            request_id=request_id,
            target_url=exc.target_url,
            status_code=exc.status_code,
            error_type=exc.error_type,
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return ApiResponse(
        success=True,
        message="User retrieved successfully",
        data=Wso2UserDetailResponse(**user),
    )


# ---------------------------------------------------------------------------
# Internal / hidden endpoints
# ---------------------------------------------------------------------------


@router.post("/internal/wso2/login", include_in_schema=False)
async def login_user(request: WSO2PasswordLoginRequest) -> dict[str, Any]:
    return await request_wso2_password_token(
        username=request.username,
        password=request.password.get_secret_value(),
        scope=request.scope,
    )
