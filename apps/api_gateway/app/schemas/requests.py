from pydantic import BaseModel, Field, SecretStr


DEFAULT_LOGIN_SCOPE = "openid profile email"


class WSO2PasswordLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="WSO2 username.")
    password: SecretStr = Field(..., min_length=1, description="WSO2 password.")
    scope: str = Field(
        DEFAULT_LOGIN_SCOPE,
        description="OIDC scopes requested from WSO2.",
    )
