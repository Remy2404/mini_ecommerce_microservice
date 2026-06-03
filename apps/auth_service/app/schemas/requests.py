"""Auth Service request schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


DEFAULT_LOGIN_SCOPE = "openid profile email"


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "username": "admin",
                "email": "admin@example.com",
                "password": "StrongPass@123",
                "first_name": "admin",
                "last_name": "admin",
            }
        },
    )

    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: SecretStr = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)


class WSO2PasswordLoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "copy-the-full-wso2-invitation-password",
                "scope": DEFAULT_LOGIN_SCOPE,
            }
        }
    )

    username: str = Field(..., min_length=1, description="WSO2 username.")
    password: SecretStr = Field(
        ...,
        min_length=1,
        description=(
            "WSO2 password. Copy the full invitation password exactly, including "
            "any trailing symbols."
        ),
    )
    scope: str = Field(
        DEFAULT_LOGIN_SCOPE,
        description="OIDC scopes requested from WSO2.",
    )

