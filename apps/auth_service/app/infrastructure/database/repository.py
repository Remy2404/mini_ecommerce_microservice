"""Auth Service repository — local database operations only.

WSO2 Identity Server is the source of truth for user identity data.
This repository handles app-owned data that is *not* managed by WSO2
(e.g. local password hashes kept for migration purposes).
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select

from apps.auth_service.app.infrastructure.database.models import (
    User,
    UserProfile,
)
from packages.config.settings import settings
from packages.database.session import session_scope


@dataclass(frozen=True)
class UserRecord:
    user_id: UUID
    email: str
    password_hash: str
    full_name: str
    is_active: bool


def _user_record(row) -> UserRecord:
    user, profile = row
    return UserRecord(
        user_id=user.id,
        email=user.email,
        password_hash=user.password_hash,
        full_name=profile.full_name,
        is_active=user.is_active,
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
