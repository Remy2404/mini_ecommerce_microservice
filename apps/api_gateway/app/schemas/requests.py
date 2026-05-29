from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


DEFAULT_LOGIN_SCOPE = "openid profile email"


def swagger_request_body(model: type[BaseModel]) -> dict[str, Any]:
    schema = model.model_json_schema()
    example = schema.pop("example", None)
    media_type: dict[str, Any] = {"schema": schema}

    if example is not None:
        media_type["example"] = example

    return {
        "requestBody": {
            "content": {
                "application/json": media_type,
            },
            "required": True,
        },
    }


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


class GatewayRegisterUserRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "username": "john.doe",
                "email": "john.doe@example.com",
                "password": "StrongPass@123",
                "first_name": "John",
                "last_name": "Doe",
            }
        },
    )

    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: SecretStr = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)


class GatewayCreateCategoryRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Electronics",
                "description": "Devices and accessories",
            }
        }
    )

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class GatewayCreateProductRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Wireless Mouse",
                "description": "Ergonomic USB-C mouse",
                "price": 19.99,
                "stock_quantity": 50,
                "category": "Electronics",
            }
        }
    )

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(ge=0)
    stock_quantity: int = Field(ge=0)
    category: str = Field(min_length=1, max_length=100)


class GatewayAddCartItemRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "product_id": "8dc75420-445d-4640-80cb-26f30a6b56b1",
                "quantity": 2,
            }
        },
    )

    product_id: UUID
    quantity: int = Field(gt=0)


class GatewayCreateOrderRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {}},
    )
