"""Auth Service routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from apps.auth_service.app.api.dependencies import get_current_token_payload
from apps.auth_service.app.application.services import AuthService, get_auth_service
from apps.auth_service.app.domain.exceptions import (
    AddressNotFoundError,
    RoleNotFoundError,
    UserNotFoundError,
)
from apps.auth_service.app.schemas.requests import (
    AssignRoleRequest,
    CreateAddressRequest,
    CreateRoleRequest,
    RegisterUserRequest,
)
from apps.auth_service.app.schemas.responses import (
    AddressResponse,
    RegisterUserResponse,
    RoleResponse,
    WSO2UserResponse,
)
from apps.api_gateway.app.schemas.requests import WSO2PasswordLoginRequest
from packages.config.settings import settings
from packages.contracts.common.schemas import ApiResponse
from packages.observability.logging import get_logger
from packages.security.wso2_login import request_wso2_password_token
from packages.security.wso2_scim import WSO2SCIMError, current_wso2_user

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


@router.post("/internal/wso2/login", include_in_schema=False)
async def login_user(request: WSO2PasswordLoginRequest) -> dict[str, Any]:
    return await request_wso2_password_token(
        username=request.username,
        password=request.password.get_secret_value(),
        scope=request.scope,
    )


@router.get("/auth/me")
async def get_me(
    request: Request,
    token_payload: dict = Depends(get_current_token_payload),
    authorization: str | None = Header(default=None),
) -> ApiResponse[WSO2UserResponse]:
    request_id = request.headers.get("x-request-id")
    access_token = (
        authorization.split(" ", 1)[1].strip()
        if authorization and authorization.lower().startswith("bearer ")
        else None
    )
    try:
        user = WSO2UserResponse(
            **await current_wso2_user(
                token_payload,
                access_token=access_token,
                request_id=request_id,
            )
        )
    except WSO2SCIMError as exc:
        logger.error(
            "WSO2 current-user lookup failed",
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

    return ApiResponse(success=True, message="User profile fetched successfully", data=user)


@router.post("/auth/addresses", status_code=status.HTTP_201_CREATED)
async def create_address(
    request: CreateAddressRequest,
    token_payload: dict = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[AddressResponse]:
    address = await service.create_address(UUID(token_payload["sub"]), request)
    return ApiResponse(success=True, message="Address created successfully", data=address)


@router.get("/auth/addresses")
async def list_addresses(
    token_payload: dict = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[list[AddressResponse]]:
    addresses = await service.list_addresses(UUID(token_payload["sub"]))
    return ApiResponse(success=True, message="Addresses fetched successfully", data=addresses)


@router.delete("/auth/addresses/{address_id}")
async def delete_address(
    address_id: UUID,
    token_payload: dict = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[dict[str, str]]:
    try:
        await service.delete_address(UUID(token_payload["sub"]), address_id)
    except AddressNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Address not found") from exc

    return ApiResponse(success=True, message="Address deleted successfully", data={"id": str(address_id)})


@router.post("/auth/roles", status_code=status.HTTP_201_CREATED)
async def create_role(
    request: CreateRoleRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[RoleResponse]:
    role = await service.create_role(request)
    return ApiResponse(success=True, message="Role created successfully", data=role)


@router.post("/auth/users/{user_id}/roles")
async def assign_role(
    user_id: UUID,
    request: AssignRoleRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[list[RoleResponse]]:
    try:
        roles = await service.assign_role(user_id, request.role_name)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Role not found") from exc

    return ApiResponse(success=True, message="Role assigned successfully", data=roles)


@router.get("/auth/users/{user_id}/roles")
async def list_user_roles(
    user_id: UUID,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[list[RoleResponse]]:
    roles = await service.list_roles(user_id)
    return ApiResponse(success=True, message="Roles fetched successfully", data=roles)
