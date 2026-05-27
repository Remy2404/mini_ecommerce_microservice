"""Application settings."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    # app settings
    app_env: str = Field(..., validation_alias="APP_ENV")
    service_version: str = Field(..., validation_alias="SERVICE_VERSION")
    log_level: str = Field(..., validation_alias="LOG_LEVEL")

    # RabbitMQ settings
    rabbitmq_host: str = Field(..., validation_alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(..., validation_alias="RABBITMQ_PORT")
    rabbitmq_user: str = Field(..., validation_alias="RABBITMQ_USER")
    rabbitmq_password: str = Field(..., validation_alias="RABBITMQ_PASSWORD")
    rabbitmq_vhost: str = Field(..., validation_alias="RABBITMQ_VHOST")
    rabbitmq_url: str = Field(..., validation_alias="RABBITMQ_URL")
    rabbitmq_exchange: str = Field(..., validation_alias="RABBITMQ_EXCHANGE")
    # WSO2 Identity Server settings
    wso2_base_url: str = Field(
        "https://localhost:9443", validation_alias="WSO2_BASE_URL"
    )
    wso2_issuer: str = Field(
        "https://localhost:9443/oauth2/token",
        validation_alias="WSO2_ISSUER",
    )
    wso2_audience: str = Field("mini-ecommerce-api", validation_alias="WSO2_AUDIENCE")
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
    wso2_client_id: str = Field(..., validation_alias="WSO2_CLIENT_ID")
    wso2_client_secret: str = Field(..., validation_alias="WSO2_CLIENT_SECRET")

    # Database settings
    postgres_user: str = Field(..., validation_alias="POSTGRES_USER")
    postgres_password: str = Field(..., validation_alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(..., validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(..., validation_alias="POSTGRES_PORT")
    products_database_name: str = Field(..., validation_alias="PRODUCTS_DATABASE_NAME")
    orders_database_name: str = Field(..., validation_alias="ORDERS_DATABASE_NAME")
    payments_database_name: str = Field(..., validation_alias="PAYMENTS_DATABASE_NAME")
    auth_database_name: str = Field("auth_db", validation_alias="AUTH_DATABASE_NAME")
    products_database_url: str = Field(..., validation_alias="PRODUCTS_DATABASE_URL")
    orders_database_url: str = Field(..., validation_alias="ORDERS_DATABASE_URL")
    payments_database_url: str = Field(..., validation_alias="PAYMENTS_DATABASE_URL")
    auth_database_url: str = Field("", validation_alias="AUTH_DATABASE_URL")

    # Valkey settings
    valkey_host: str = Field(..., validation_alias="VALKEY_HOST")
    valkey_port: int = Field(..., validation_alias="VALKEY_PORT")
    valkey_password: str = Field("", validation_alias="VALKEY_PASSWORD")
    valkey_url: str = Field(..., validation_alias="VALKEY_URL")

    # open telemetry settings
    otel_exporter_otlp_endpoint: str = Field(
        ..., validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_exporter_otlp_protocol: str = Field(
        ..., validation_alias="OTEL_EXPORTER_OTLP_PROTOCOL"
    )
    otel_exporter_otlp_headers: str = Field(
        "", validation_alias="OTEL_EXPORTER_OTLP_HEADERS"
    )
    otel_resource_attributes: str = Field(
        ..., validation_alias="OTEL_RESOURCE_ATTRIBUTES"
    )
    otel_traces_sampler: str = Field(
        "parentbased_always_on", validation_alias="OTEL_TRACES_SAMPLER"
    )

    # Service names
    api_gateway_service_name: str = Field(
        ..., validation_alias="API_GATEWAY_SERVICE_NAME"
    )
    auth_service_name: str = Field("auth-service", validation_alias="AUTH_SERVICE_NAME")
    product_service_name: str = Field(..., validation_alias="PRODUCT_SERVICE_NAME")
    cart_service_name: str = Field(..., validation_alias="CART_SERVICE_NAME")
    order_service_name: str = Field(..., validation_alias="ORDER_SERVICE_NAME")
    payment_service_name: str = Field(..., validation_alias="PAYMENT_SERVICE_NAME")

    # service port
    api_gateway_port: int = Field(..., validation_alias="API_GATEWAY_PORT")
    auth_service_port: int = Field(8005, validation_alias="AUTH_SERVICE_PORT")
    product_service_port: int = Field(..., validation_alias="PRODUCT_SERVICE_PORT")
    cart_service_port: int = Field(..., validation_alias="CART_SERVICE_PORT")
    order_service_port: int = Field(..., validation_alias="ORDER_SERVICE_PORT")
    payment_service_port: int = Field(..., validation_alias="PAYMENT_SERVICE_PORT")

    # Internal Service URLs

    product_service_url: str = Field(..., validation_alias="PRODUCT_SERVICE_URL")
    auth_service_url: str = Field(
        "http://localhost:8005",
        validation_alias="AUTH_SERVICE_URL",
    )
    cart_service_url: str = Field(..., validation_alias="CART_SERVICE_URL")
    order_service_url: str = Field(..., validation_alias="ORDER_SERVICE_URL")
    payment_service_url: str = Field(..., validation_alias="PAYMENT_SERVICE_URL")

    # API Gateway settings
    gateway_auth_enabled: bool = Field(False, validation_alias="GATEWAY_AUTH_ENABLED")
    gateway_request_timeout_seconds: float = Field(
        10.0,
        validation_alias="GATEWAY_REQUEST_TIMEOUT_SECONDS",
    )
    wso2_request_timeout_seconds: float = Field(
        10.0,
        validation_alias="WSO2_REQUEST_TIMEOUT_SECONDS",
    )
    wso2_verify_ssl: bool = Field(False, validation_alias="WSO2_VERIFY_SSL")
    gateway_rate_limit_enabled: bool = Field(
        False,
        validation_alias="GATEWAY_RATE_LIMIT_ENABLED",
    )
    gateway_rate_limit_per_minute: int = Field(
        60,
        validation_alias="GATEWAY_RATE_LIMIT_PER_MINUTE",
    )

    # jwt settings
    jwt_algorithm: str = Field(..., validation_alias="JWT_ALGORITHM")
    jwt_secret_key: SecretStr = Field("", validation_alias="JWT_SECRET_KEY")
    access_token_expire_minutes: int = Field(
        ..., validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    cors_allowed_origins: str = Field(..., validation_alias="CORS_ALLOWED_ORIGINS")
    # Certificate Validation
    tls_enabled: bool = Field(..., validation_alias="TLS_ENABLED")
    cert_validation_enabled: bool = Field(
        ..., validation_alias="CERT_VALIDATION_ENABLED"
    )
    ca_cert_path: str = Field(..., validation_alias="CA_CERT_PATH")
    client_cert_path: str = Field(..., validation_alias="CLIENT_CERT_PATH")
    client_key_path: str = Field(..., validation_alias="CLIENT_KEY_PATH")

    # Payment Simulation
    payment_success_rate: float = Field(..., validation_alias="PAYMENT_SUCCESS_RATE")
    payment_min_delay_ms: int = Field(..., validation_alias="PAYMENT_MIN_DELAY_MS")
    payment_max_delay_ms: int = Field(..., validation_alias="PAYMENT_MAX_DELAY_MS")

    # Caching settings
    product_cache_ttl_seconds: int = Field(
        ..., validation_alias="PRODUCT_CACHE_TTL_SECONDS"
    )
    cart_cache_ttl_seconds: int = Field(..., validation_alias="CART_CACHE_TTL_SECONDS")
    rate_limit_ttl_seconds: int = Field(..., validation_alias="RATE_LIMIT_TTL_SECONDS")

    # Rate limiting settings
    rate_limit_enabled: bool = Field(..., validation_alias="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(
        ..., validation_alias="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )

    # Object storage settings
    object_storage_endpoint_url: str | None = Field(
        None,
        validation_alias="OBJECT_STORAGE_ENDPOINT_URL",
    )
    object_storage_access_key_id: str | None = Field(
        None,
        validation_alias="OBJECT_STORAGE_ACCESS_KEY_ID",
    )
    object_storage_secret_access_key: str | None = Field(
        None,
        validation_alias="OBJECT_STORAGE_SECRET_ACCESS_KEY",
    )
    object_storage_region: str = Field(
        "us-east-1",
        validation_alias="OBJECT_STORAGE_REGION",
    )
    object_storage_bucket_name: str = Field(
        "mini-ecommerce-media",
        validation_alias="OBJECT_STORAGE_BUCKET_NAME",
    )
    object_storage_public_base_url: str | None = Field(
        None,
        validation_alias="OBJECT_STORAGE_PUBLIC_BASE_URL",
    )
    object_storage_presigned_url_expire_seconds: int = Field(
        900,
        validation_alias="OBJECT_STORAGE_PRESIGNED_URL_EXPIRE_SECONDS",
    )
    object_storage_upload_max_bytes: int = Field(
        5 * 1024 * 1024,
        validation_alias="OBJECT_STORAGE_UPLOAD_MAX_BYTES",
    )

    # Image processing settings
    thumbnail_max_width: int = Field(
        300,
        validation_alias="THUMBNAIL_MAX_WIDTH",
    )
    thumbnail_max_height: int = Field(
        300,
        validation_alias="THUMBNAIL_MAX_HEIGHT",
    )
    thumbnail_quality: int = Field(
        85,
        validation_alias="THUMBNAIL_QUALITY",
    )

    # RabbitMQ Routing Keys
    order_created_routing_key: str = Field(
        ..., validation_alias="ORDER_CREATED_ROUTING_KEY"
    )
    payment_success_routing_key: str = Field(
        ..., validation_alias="PAYMENT_SUCCESS_ROUTING_KEY"
    )
    payment_failed_routing_key: str = Field(
        ..., validation_alias="PAYMENT_FAILED_ROUTING_KEY"
    )
    order_confirmed_routing_key: str = Field(
        ..., validation_alias="ORDER_CONFIRMED_ROUTING_KEY"
    )
    order_cancelled_routing_key: str = Field(
        ..., validation_alias="ORDER_CANCELLED_ROUTING_KEY"
    )
    cart_restored_routing_key: str = Field(
        ..., validation_alias="CART_RESTORED_ROUTING_KEY"
    )
    # RabbitMQ Queues
    order_created_queue: str = Field(..., validation_alias="ORDER_CREATED_QUEUE")
    payment_result_queue: str = Field(..., validation_alias="PAYMENT_RESULT_QUEUE")
    cart_restore_queue: str = Field(..., validation_alias="CART_RESTORE_QUEUE")
    dead_letter_queue: str = Field(..., validation_alias="DEAD_LETTER_QUEUE")

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def api_gateway(self) -> str:
        """Backward-compatible alias for existing service-name references."""
        return self.api_gateway_service_name


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
