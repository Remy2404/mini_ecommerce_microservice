"""Token adapter for Auth Service."""

from uuid import UUID

from packages.security.jwt import create_access_token


def issue_user_token(user_id: UUID, *, email: str, roles: list[str]) -> str:
    return create_access_token(
        subject=str(user_id),
        roles=roles,
        extra_claims={"email": email},
    )
