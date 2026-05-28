"""Small role and ownership permission helpers."""

from collections.abc import Iterable

from packages.errors.exceptions import ForbiddenError


def has_role(user_roles: Iterable[str], required_role: str) -> bool:
    return required_role in set(user_roles)


def require_role(user_roles: Iterable[str], required_role: str) -> None:
    if not has_role(user_roles, required_role):
        raise ForbiddenError("Missing required role", required_role=required_role)


def require_owner_or_role(
    *,
    resource_owner_id: str,
    current_user_id: str,
    user_roles: Iterable[str],
    role: str = "admin",
) -> None:
    if resource_owner_id == current_user_id:
        return

    require_role(user_roles, role)
