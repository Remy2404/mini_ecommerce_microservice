"""Cart Service settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = Field(..., validation_alias="APP_ENV")
    service_version: str = Field(..., validation_alias="SERVICE_VERSION")
    log_level: str = Field(..., validation_alias="LOG_LEVEL")

    product_service_url: str = Field(..., validation_alias="PRODUCT_SERVICE_URL")
    gateway_request_timeout_seconds: float = Field(
        10.0,
        validation_alias="GATEWAY_REQUEST_TIMEOUT_SECONDS",
    )
    cart_cache_ttl_seconds: int = Field(
        ...,
        validation_alias="CART_CACHE_TTL_SECONDS",
    )
    valkey_url: str = Field(..., validation_alias="VALKEY_URL")

    otel_exporter_otlp_endpoint: str = Field(
        ..., validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    cart_service_name: str = Field("cart-service", validation_alias="CART_SERVICE_NAME")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
