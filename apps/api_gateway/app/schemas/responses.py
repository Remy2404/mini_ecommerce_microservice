"""Gateway Swagger response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class Wso2UserProfile(BaseModel):
    id: str
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    active: bool = True
    roles: list[str] = Field(default_factory=list)


class Wso2UsersListResponse(BaseModel):
    total_results: int = 0
    start_index: int = 1
    items_per_page: int = 0
    users: list[Wso2UserProfile] = Field(default_factory=list)


class Wso2UserDetailResponse(BaseModel):
    user: Wso2UserProfile


class GatewayWso2UsersListResponse(BaseModel):
    success: bool
    message: str
    data: Wso2UsersListResponse


class GatewayWso2UserDetailResponse(BaseModel):
    success: bool
    message: str
    data: Wso2UserDetailResponse


class WSO2TokenResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    id_token: str | None = None
    scope: str | None = None
