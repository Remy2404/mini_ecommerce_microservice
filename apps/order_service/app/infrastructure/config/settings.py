"""Order Service settings."""

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

    orders_database_url: str = Field(..., validation_alias="ORDERS_DATABASE_URL")
    valkey_url: str = Field(..., validation_alias="VALKEY_URL")

    rabbitmq_url: str = Field(..., validation_alias="RABBITMQ_URL")
    rabbitmq_retry_max_attempts: int = Field(
        3,
        validation_alias="RABBITMQ_RETRY_MAX_ATTEMPTS",
    )
    rabbitmq_retry_delay_ms: int = Field(
        5000,
        validation_alias="RABBITMQ_RETRY_DELAY_MS",
    )
    rabbitmq_retry_backoff_multiplier: float = Field(
        2.0,
        validation_alias="RABBITMQ_RETRY_BACKOFF_MULTIPLIER",
    )

    otel_exporter_otlp_endpoint: str = Field(
        ..., validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    order_service_name: str = Field(
        "order-service", validation_alias="ORDER_SERVICE_NAME"
    )

    order_created_routing_key: str = Field(
        "order.created.v1",
        validation_alias="ORDER_CREATED_ROUTING_KEY",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
