from fastapi import APIRouter, HTTPException, Query, Request

from apps.auth_service.app.api.routes._common import get_request_id
from apps.auth_service.app.infrastructure.observability.logging import get_logger
from apps.auth_service.app.infrastructure.security.wso2_scim import WSO2SCIMError
from apps.auth_service.app.schemas.common import ApiResponse
from apps.auth_service.app.schemas.responses import (
    Wso2UserDetailResponse,
    Wso2UsersListResponse,
)

router = APIRouter(prefix="/auth")
logger = get_logger(__name__)


@router.get(
    "/users",
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
    request_id = get_request_id(request)
    try:
        from apps.auth_service.app.api import routes as routes_module

        result = await routes_module.filter_wso2_users(
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
    "/users/search",
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
    request_id = get_request_id(request)
    try:
        from apps.auth_service.app.api import routes as routes_module

        result = await routes_module.search_wso2_users(
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
    "/users/{user_id}",
    response_model=ApiResponse[Wso2UserDetailResponse],
    summary="Get user by WSO2 SCIM ID",
    description="Fetches a single user from WSO2 by SCIM2 user ID. Scope: internal_user_mgt_view.",
)
async def get_user_by_id_route(
    request: Request,
    user_id: str,
) -> ApiResponse[Wso2UserDetailResponse]:
    request_id = get_request_id(request)
    try:
        from apps.auth_service.app.api import routes as routes_module

        user = await routes_module.get_wso2_user_by_id(user_id, request_id=request_id)
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
