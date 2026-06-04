"""Auth Service settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for Auth Service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = Field(..., validation_alias="APP_ENV")
    service_version: str = Field(..., validation_alias="SERVICE_VERSION")
    log_level: str = Field(..., validation_alias="LOG_LEVEL")

    postgres_user: str = Field(..., validation_alias="POSTGRES_USER")
    postgres_password: str = Field(..., validation_alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(..., validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(..., validation_alias="POSTGRES_PORT")
    auth_database_name: str = Field("auth_db", validation_alias="AUTH_DATABASE_NAME")
    auth_database_url: str = Field("", validation_alias="AUTH_DATABASE_URL")

    wso2_base_url: str = Field(
        "https://localhost:9443",
        validation_alias="WSO2_BASE_URL",
    )
    wso2_issuer: str = Field(
        "https://localhost:9443/oauth2/token",
        validation_alias="WSO2_ISSUER",
    )
    wso2_audience: str = Field(..., validation_alias="WSO2_AUDIENCE")
    wso2_jwks_url: str = Field(
        "https://localhost:9443/oauth2/jwks",
        validation_alias="WSO2_JWKS_URL",
    )
    wso2_token_url: str = Field(
        "https://localhost:9443/oauth2/token",
        validation_alias="WSO2_TOKEN_URL",
    )
    wso2_introspection_url: str = Field(
        "https://localhost:9443/oauth2/introspect",
        validation_alias="WSO2_INTROSPECTION_URL",
    )
    wso2_userinfo_url: str = Field(
        "https://localhost:9443/oauth2/userinfo",
        validation_alias="WSO2_USERINFO_URL",
    )
    wso2_client_id: str = Field(..., validation_alias="WSO2_CLIENT_ID")
    wso2_client_secret: str = Field(..., validation_alias="WSO2_CLIENT_SECRET")
    wso2_scim_create_scope: str = Field(
        "internal_user_mgt_create",
        validation_alias="WSO2_SCIM_CREATE_SCOPE",
    )
    wso2_scim_view_scope: str = Field(
        "internal_user_mgt_view",
        validation_alias="WSO2_SCIM_VIEW_SCOPE",
    )
    wso2_scim_list_scope: str = Field(
        "internal_user_mgt_list",
        validation_alias="WSO2_SCIM_LIST_SCOPE",
    )
    wso2_request_timeout_seconds: float = Field(
        10.0,
        validation_alias="WSO2_REQUEST_TIMEOUT_SECONDS",
    )
    wso2_verify_ssl: bool = Field(False, validation_alias="WSO2_VERIFY_SSL")

    jwt_algorithm: str = Field(..., validation_alias="JWT_ALGORITHM")

    otel_exporter_otlp_endpoint: str = Field(
        ..., validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    auth_service_name: str = Field("auth-service", validation_alias="AUTH_SERVICE_NAME")

    def service_database_url(self, database_name: str) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{database_name}"
        )

    @property
    def resolved_auth_database_url(self) -> str:
        return self.auth_database_url or self.service_database_url(
            self.auth_database_name
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
