"""Gateway Swagger response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr


class DetailErrorResponse(BaseModel):
    detail: str


class WSO2UserResponse(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    roles: list[str]


class RegisterUserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    message: str


class GatewayRegisterUserResponse(BaseModel):
    success: bool
    message: str
    data: RegisterUserResponse


class WSO2TokenResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    id_token: str | None = None
    scope: str | None = None
