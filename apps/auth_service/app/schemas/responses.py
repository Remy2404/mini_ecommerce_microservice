"""Auth Service response schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr


class RoleResponse(BaseModel):
    role_id: UUID
    name: str
    description: str | None = None


class UserProfileResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    roles: list[str]


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserProfileResponse


class AddressResponse(BaseModel):
    address_id: UUID
    user_id: UUID
    line1: str
    line2: str | None = None
    city: str
    state: str | None = None
    postal_code: str
    country: str
    phone: str | None = None
