"""Auth Service value objects."""

from __future__ import annotations

from dataclasses import dataclass


def _normalize_text(value: str) -> str:
    return value.strip()


@dataclass(frozen=True, slots=True)
class Username:
    value: str

    def __post_init__(self) -> None:
        normalized = _normalize_text(self.value)
        if len(normalized) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(normalized) > 80:
            raise ValueError("Username must be 80 characters or fewer")
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_value(cls, value: Username | str) -> "Username":
        if isinstance(value, Username):
            return value
        return cls(value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        normalized = _normalize_text(self.value).lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Invalid email address")
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_value(cls, value: EmailAddress | str) -> "EmailAddress":
        if isinstance(value, EmailAddress):
            return value
        return cls(value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class FullName:
    first_name: str
    last_name: str

    def __post_init__(self) -> None:
        first_name = _normalize_text(self.first_name)
        last_name = _normalize_text(self.last_name)
        if not first_name:
            raise ValueError("First name cannot be empty")
        if not last_name:
            raise ValueError("Last name cannot be empty")
        if len(first_name) > 80:
            raise ValueError("First name must be 80 characters or fewer")
        if len(last_name) > 80:
            raise ValueError("Last name must be 80 characters or fewer")
        object.__setattr__(self, "first_name", first_name)
        object.__setattr__(self, "last_name", last_name)

    @classmethod
    def from_value(cls, value: FullName | tuple[str, str]) -> "FullName":
        if isinstance(value, FullName):
            return value
        first_name, last_name = value
        return cls(first_name=first_name, last_name=last_name)

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
