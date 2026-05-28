"""Auth Service policy checks."""

from uuid import UUID

from packages.errors.exceptions import ForbiddenError


def ensure_address_owner(*, current_user_id: UUID, address_user_id: UUID) -> None:
    if current_user_id != address_user_id:
        raise ForbiddenError("Address does not belong to current user")
