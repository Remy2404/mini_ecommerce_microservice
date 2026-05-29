"""Auth Service orchestration."""

from typing import Any
from uuid import UUID

from apps.auth_service.app.domain.exceptions import (
    AddressNotFoundError,
    RoleNotFoundError,
    UserNotFoundError,
)
from apps.auth_service.app.infrastructure.database.repository import AuthRepository
from apps.auth_service.app.schemas.requests import (
    CreateAddressRequest,
    CreateRoleRequest,
    LoginRequest,
    RegisterUserRequest,
)
from apps.auth_service.app.schemas.responses import (
    AddressResponse,
    RegisterUserResponse,
    RoleResponse,
    UserProfileResponse,
)
from packages.security.wso2_login import request_wso2_password_token
from packages.security.wso2_scim import register_wso2_user


class AuthService:
    def __init__(self, repository: AuthRepository | None = None) -> None:
        self.repository = repository or AuthRepository()

    async def register_user(
        self,
        request: RegisterUserRequest,
        *,
        request_id: str | None = None,
    ) -> RegisterUserResponse:
        user = await register_wso2_user(
            username=request.username,
            email=str(request.email),
            password=request.password.get_secret_value(),
            given_name=request.given_name,
            family_name=request.family_name,
            request_id=request_id,
        )
        return RegisterUserResponse(**user)

    async def login_user(self, request: LoginRequest) -> dict[str, Any]:
        return await request_wso2_password_token(
            username=str(request.email),
            password=request.password.get_secret_value(),
            scope="openid profile email",
        )

    async def get_user_profile(self, user_id: UUID) -> UserProfileResponse:
        user = await self.repository.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundError

        roles = await self.repository.list_roles(user_id)
        return UserProfileResponse(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            roles=[role.name for role in roles],
        )

    async def create_address(
        self,
        user_id: UUID,
        request: CreateAddressRequest,
    ) -> AddressResponse:
        if await self.repository.get_user_by_id(user_id) is None:
            raise UserNotFoundError

        return await self.repository.create_address(user_id, request)

    async def list_addresses(self, user_id: UUID) -> list[AddressResponse]:
        return await self.repository.list_addresses(user_id)

    async def delete_address(self, user_id: UUID, address_id: UUID) -> None:
        deleted = await self.repository.delete_address(user_id, address_id)
        if not deleted:
            raise AddressNotFoundError

    async def create_role(self, request: CreateRoleRequest) -> RoleResponse:
        return await self.repository.ensure_role(request.name, request.description)

    async def assign_role(self, user_id: UUID, role_name: str) -> list[RoleResponse]:
        if await self.repository.get_user_by_id(user_id) is None:
            raise UserNotFoundError

        if await self.repository.get_role(role_name) is None:
            raise RoleNotFoundError

        await self.repository.assign_role(user_id, role_name)
        return await self.repository.list_roles(user_id)

    async def list_roles(self, user_id: UUID) -> list[RoleResponse]:
        return await self.repository.list_roles(user_id)


def get_auth_service() -> AuthService:
    return AuthService()
