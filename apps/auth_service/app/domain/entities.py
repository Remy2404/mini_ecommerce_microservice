"""Pure auth domain entities."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: UUID
    email: str
    roles: tuple[str, ...]
