"""Auth Service routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from apps.auth_service.app.api.dependencies import get_current_token_payload
from apps.auth_service.app.application.services import AuthService, get_auth_service
from apps.auth_service.app.domain.exceptions import (
    AddressNotFoundError,
    InvalidCredentialsError,
    RoleNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from apps.auth_service.app.schemas.requests import (
    AssignRoleRequest,
    CreateAddressRequest,
    CreateRoleRequest,
    LoginRequest,
    RegisterUserRequest,
)
from apps.auth_service.app.schemas.responses import (
    AddressResponse,
    AuthTokenResponse,
    RoleResponse,
    UserProfileResponse,
)
from packages.config.settings import settings
from packages.contracts.common.schemas import ApiResponse

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.auth_service_name}


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    request: RegisterUserRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[UserProfileResponse]:
    try:
        user = await service.register_user(request)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="User already exists") from exc

    return ApiResponse(
        success=True,
        message="User registered successfully",
        data=user,
    )


@router.post("/auth/login")
async def login_user(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[AuthTokenResponse]:
    try:
        token = await service.login_user(request)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail="Invalid credentials") from exc

    return ApiResponse(success=True, message="Login successful", data=token)


@router.get("/auth/me")
async def get_me(
    token_payload: dict = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[UserProfileResponse]:
    try:
        user = await service.get_user_profile(UUID(token_payload["sub"]))
    except (ValueError, UserNotFoundError) as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc

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
