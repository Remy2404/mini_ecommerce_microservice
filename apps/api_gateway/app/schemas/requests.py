from pydantic import BaseModel, ConfigDict, Field, SecretStr


DEFAULT_LOGIN_SCOPE = "openid profile email"


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
