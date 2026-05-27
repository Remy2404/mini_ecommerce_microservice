"""Auth Service request schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr


class CreateAddressRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line1: str = Field(min_length=1, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    postal_code: str = Field(min_length=1, max_length=40)
    country: str = Field(min_length=2, max_length=2)
    phone: str | None = Field(default=None, max_length=40)


class CreateRoleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)


class AssignRoleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_name: str = Field(min_length=1, max_length=80)
