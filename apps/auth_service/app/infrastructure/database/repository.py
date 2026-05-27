"""Auth Service repository."""

from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth_service.app.infrastructure.database.models import (
    Role,
    User,
    UserAddress,
    UserProfile,
    UserRole,
)
from apps.auth_service.app.schemas.requests import CreateAddressRequest
from apps.auth_service.app.schemas.responses import AddressResponse, RoleResponse
from packages.config.settings import settings
from packages.database.session import session_scope


@dataclass(frozen=True)
class UserRecord:
    user_id: UUID
    email: str
    password_hash: str
    full_name: str
    is_active: bool


def _role_response(role: Role) -> RoleResponse:
    return RoleResponse(role_id=role.id, name=role.name, description=role.description)


def _address_response(address: UserAddress) -> AddressResponse:
    return AddressResponse(
        address_id=address.id,
        user_id=address.user_id,
        line1=address.line1,
        line2=address.line2,
        city=address.city,
        state=address.state,
        postal_code=address.postal_code,
        country=address.country,
        phone=address.phone,
    )


class AuthRepository:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or settings.resolved_auth_database_url

    async def _session(self):
        if not self.database_url:
            raise RuntimeError("AUTH_DATABASE_URL must be configured")
        return session_scope(self.database_url)

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        async with await self._session() as session:
            result = await session.execute(
                select(User, UserProfile).join(UserProfile).where(User.email == email)
            )
            row = result.first()
        return _user_record(row) if row else None

    async def get_user_by_id(self, user_id: UUID) -> UserRecord | None:
        async with await self._session() as session:
            result = await session.execute(
                select(User, UserProfile).join(UserProfile).where(User.id == user_id)
            )
            row = result.first()
        return _user_record(row) if row else None

    async def create_user(
        self,
        *,
        user_id: UUID,
        email: str,
        password_hash: str,
        full_name: str,
    ) -> None:
        async with await self._session() as session:
            user = User(id=user_id, email=email, password_hash=password_hash)
            session.add(user)
            session.add(UserProfile(user_id=user_id, full_name=full_name))

    async def ensure_role(self, name: str, description: str | None) -> RoleResponse:
        async with await self._session() as session:
            role = await _get_role_model(session, name)
            if role is None:
                role = Role(id=uuid4(), name=name, description=description)
                session.add(role)
                await session.flush()
            return _role_response(role)

    async def get_role(self, name: str) -> RoleResponse | None:
        async with await self._session() as session:
            role = await _get_role_model(session, name)
            return _role_response(role) if role else None

    async def assign_role(self, user_id: UUID, role_name: str) -> None:
        async with await self._session() as session:
            role = await _get_role_model(session, role_name)
            if role is None:
                return
            existing = await session.get(UserRole, {"user_id": user_id, "role_id": role.id})
            if existing is None:
                session.add(UserRole(user_id=user_id, role_id=role.id))

    async def list_roles(self, user_id: UUID) -> list[RoleResponse]:
        async with await self._session() as session:
            result = await session.execute(
                select(Role)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == user_id)
                .order_by(Role.name)
            )
            roles = result.scalars().all()
        return [_role_response(role) for role in roles]

    async def create_address(
        self,
        user_id: UUID,
        request: CreateAddressRequest,
    ) -> AddressResponse:
        async with await self._session() as session:
            address = UserAddress(
                id=uuid4(),
                user_id=user_id,
                line1=request.line1,
                line2=request.line2,
                city=request.city,
                state=request.state,
                postal_code=request.postal_code,
                country=request.country.upper(),
                phone=request.phone,
            )
            session.add(address)
            await session.flush()
            return _address_response(address)

    async def list_addresses(self, user_id: UUID) -> list[AddressResponse]:
        async with await self._session() as session:
            result = await session.execute(
                select(UserAddress)
                .where(UserAddress.user_id == user_id)
                .order_by(UserAddress.created_at.desc())
            )
            addresses = result.scalars().all()
        return [_address_response(address) for address in addresses]

    async def delete_address(self, user_id: UUID, address_id: UUID) -> bool:
        async with await self._session() as session:
            result = await session.execute(
                delete(UserAddress).where(
                    UserAddress.id == address_id,
                    UserAddress.user_id == user_id,
                )
            )
            return bool(result.rowcount)


def _user_record(row) -> UserRecord:
    user, profile = row
    return UserRecord(
        user_id=user.id,
        email=user.email,
        password_hash=user.password_hash,
        full_name=profile.full_name,
        is_active=user.is_active,
    )


async def _get_role_model(session: AsyncSession, name: str) -> Role | None:
    result = await session.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()
