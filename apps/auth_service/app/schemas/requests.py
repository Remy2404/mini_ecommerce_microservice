"""Auth Service request schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


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
