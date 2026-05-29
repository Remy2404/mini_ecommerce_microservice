"""Auth Service request and response DTOs."""

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
    RegisterUserResponse,
    RoleResponse,
    UserProfileResponse,
    WSO2UserResponse,
)

__all__ = [
    "AddressResponse",
    "AssignRoleRequest",
    "AuthTokenResponse",
    "CreateAddressRequest",
    "CreateRoleRequest",
    "LoginRequest",
    "RegisterUserResponse",
    "RegisterUserRequest",
    "RoleResponse",
    "UserProfileResponse",
    "WSO2UserResponse",
]
