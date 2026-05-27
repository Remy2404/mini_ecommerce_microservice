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
    RoleResponse,
    UserProfileResponse,
)

__all__ = [
    "AddressResponse",
    "AssignRoleRequest",
    "AuthTokenResponse",
    "CreateAddressRequest",
    "CreateRoleRequest",
    "LoginRequest",
    "RegisterUserRequest",
    "RoleResponse",
    "UserProfileResponse",
]
