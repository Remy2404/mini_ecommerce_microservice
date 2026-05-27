"""Auth Service orchestration."""

from uuid import UUID, uuid4

from apps.auth_service.app.domain.exceptions import (
    AddressNotFoundError,
    InvalidCredentialsError,
    RoleNotFoundError,
    UserAlreadyExistsError,
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
    AuthTokenResponse,
    RoleResponse,
    UserProfileResponse,
)
from packages.security.jwt import create_access_token
from packages.security.passwords import hash_password, verify_password


class AuthService:
    def __init__(self, repository: AuthRepository | None = None) -> None:
        self.repository = repository or AuthRepository()

    async def register_user(self, request: RegisterUserRequest) -> UserProfileResponse:
        existing = await self.repository.get_user_by_email(request.email)
        if existing is not None:
            raise UserAlreadyExistsError

        user_id = uuid4()
        password_hash = hash_password(request.password.get_secret_value())
        await self.repository.create_user(
            user_id=user_id,
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name,
        )
        await self.repository.ensure_role("customer", "Default customer role")
        await self.repository.assign_role(user_id, "customer")
        return await self.get_user_profile(user_id)

    async def login_user(self, request: LoginRequest) -> AuthTokenResponse:
        user = await self.repository.get_user_by_email(request.email)
        if user is None or not verify_password(
            request.password.get_secret_value(),
            user.password_hash,
        ):
            raise InvalidCredentialsError

        roles = await self.repository.list_roles(user.user_id)
        access_token = create_access_token(
            subject=str(user.user_id),
            roles=[role.name for role in roles],
            extra_claims={"email": user.email},
        )
        return AuthTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            user=await self.get_user_profile(user.user_id),
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
