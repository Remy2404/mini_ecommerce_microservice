"""Pure auth domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field

from apps.auth_service.app.domain.value_objects import EmailAddress, FullName, Username


@dataclass(slots=True)
class RegisteredUser:
    user_id: str
    username: Username | str
    email: EmailAddress | str
    full_name: FullName | tuple[str, str]
    message: str = field(default="User registered successfully")

    def __post_init__(self) -> None:
        self.username = Username.from_value(self.username)
        self.email = EmailAddress.from_value(self.email)
        self.full_name = FullName.from_value(self.full_name)
        self.user_id = str(self.user_id)
        if not self.user_id.strip():
            raise ValueError("User id cannot be empty")
        self.message = self.message.strip() or "User registered successfully"

    @classmethod
    def from_registration_result(
        cls,
        payload: dict[str, object],
        *,
        requested_username: str,
        requested_email: str,
        first_name: str,
        last_name: str,
    ) -> "RegisteredUser":
        return cls(
            user_id=str(payload.get("id", "")),
            username=str(payload.get("username", requested_username)),
            email=str(payload.get("email", requested_email)),
            full_name=(first_name, last_name),
            message=str(payload.get("message", "User registered successfully")),
        )

    def to_response_payload(self) -> dict[str, str]:
        return {
            "id": self.user_id,
            "username": str(self.username),
            "email": str(self.email),
            "message": self.message,
        }


AuthenticatedUser = RegisteredUser
