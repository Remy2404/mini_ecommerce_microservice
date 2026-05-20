"""Application settings."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    #app settings
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
    wso2_base_url: str = Field(..., validation_alias="WSO2_BASE_URL")
    wso2_issuer: str = Field(..., validation_alias="WSO2_ISSUER")
    wso2_audience: str = Field(..., validation_alias="WSO2_AUDIENCE")
    wso2_jwks_url: str = Field(..., validation_alias="WSO2_JWKS_URL")
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
    products_database_url: str = Field(..., validation_alias="PRODUCTS_DATABASE_URL")
    orders_database_url: str = Field(..., validation_alias="ORDERS_DATABASE_URL")
    payments_database_url: str = Field(..., validation_alias="PAYMENTS_DATABASE_URL")

    # Valkey settings
    valkey_host: str = Field(..., validation_alias="VALKEY_HOST")
    valkey_port: int = Field(..., validation_alias="VALKEY_PORT")
    valkey_password: str = Field("", validation_alias="VALKEY_PASSWORD")
    valkey_url: str = Field(..., validation_alias="VALKEY_URL")

    # open telemetry settings
    otel_exporter_otlp_endpoint: str = Field(..., validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_exporter_otlp_protocol: str = Field(..., validation_alias="OTEL_EXPORTER_OTLP_PROTOCOL")
    otel_exporter_otlp_headers: str = Field("", validation_alias="OTEL_EXPORTER_OTLP_HEADERS")
    otel_resource_attributes: str = Field(..., validation_alias="OTEL_RESOURCE_ATTRIBUTES")
    otel_traces_sampler: str = Field("parentbased_always_on", validation_alias="OTEL_TRACES_SAMPLER")

    # Service names
    api_gateway: str = Field(..., validation_alias="API_GATEWAY_SERVICE_NAME")
    product_service_name: str = Field(..., validation_alias="PRODUCT_SERVICE_NAME")
    cart_service_name: str = Field(..., validation_alias="CART_SERVICE_NAME")
    order_service_name: str = Field(..., validation_alias="ORDER_SERVICE_NAME")
    payment_service_name: str = Field(..., validation_alias="PAYMENT_SERVICE_NAME")

    # service port
    api_gateway_port: int = Field(..., validation_alias="API_GATEWAY_PORT")
    product_service_port: int = Field(..., validation_alias="PRODUCT_SERVICE_PORT")
    cart_service_port: int = Field(..., validation_alias="CART_SERVICE_PORT")
    order_service_port: int = Field(..., validation_alias="ORDER_SERVICE_PORT")
    payment_service_port: int = Field(..., validation_alias="PAYMENT_SERVICE_PORT")

    # Internal Service URLs

    product_service_url: str = Field(..., validation_alias="PRODUCT_SERVICE_URL")
    cart_service_url: str = Field(..., validation_alias="CART_SERVICE_URL")
    order_service_url: str = Field(..., validation_alias="ORDER_SERVICE_URL")
    payment_service_url: str = Field(..., validation_alias="PAYMENT_SERVICE_URL")

    # jwt settings
    jwt_algorithm: str = Field(..., validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(..., validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    cors_allowed_origins: str = Field(..., validation_alias="CORS_ALLOWED_ORIGINS")
    # Certificate Validation
    tls_enabled: bool = Field(..., validation_alias="TLS_ENABLED")
    cert_validation_enabled: bool = Field(..., validation_alias="CERT_VALIDATION_ENABLED")
    ca_cert_path: str = Field(..., validation_alias="CA_CERT_PATH")
    client_cert_path: str = Field(..., validation_alias="CLIENT_CERT_PATH")
    client_key_path: str = Field(..., validation_alias="CLIENT_KEY_PATH")

    # Payment Simulation
    payment_success_rate: float = Field(..., validation_alias="PAYMENT_SUCCESS_RATE")
    payment_min_delay_ms: int = Field(..., validation_alias="PAYMENT_MIN_DELAY_MS")
    payment_max_delay_ms: int = Field(..., validation_alias="PAYMENT_MAX_DELAY_MS")

    # Caching settings
    product_cache_ttl_seconds: int = Field(..., validation_alias="PRODUCT_CACHE_TTL_SECONDS")
    cart_cache_ttl_seconds: int = Field(..., validation_alias="CART_CACHE_TTL_SECONDS")
    rate_limit_ttl_seconds: int = Field(..., validation_alias="RATE_LIMIT_TTL_SECONDS")

    # Rate limiting settings
    rate_limit_enabled: bool = Field(..., validation_alias="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(..., validation_alias="RATE_LIMIT_REQUESTS_PER_MINUTE")

    # RabbitMQ Routing Keys
    order_created_routing_key: str = Field(..., validation_alias="ORDER_CREATED_ROUTING_KEY")
    payment_success_routing_key: str = Field(..., validation_alias="PAYMENT_SUCCESS_ROUTING_KEY")
    payment_failed_routing_key: str = Field(..., validation_alias="PAYMENT_FAILED_ROUTING_KEY")
    order_confirmed_routing_key: str = Field(..., validation_alias="ORDER_CONFIRMED_ROUTING_KEY")
    order_cancelled_routing_key: str = Field(..., validation_alias="ORDER_CANCELLED_ROUTING_KEY")
    cart_restored_routing_key: str = Field(..., validation_alias="CART_RESTORED_ROUTING_KEY")
    # RabbitMQ Queues
    order_created_queue: str = Field(..., validation_alias="ORDER_CREATED_QUEUE")
    payment_result_queue: str = Field(..., validation_alias="PAYMENT_RESULT_QUEUE")
    cart_restore_queue: str = Field(..., validation_alias="CART_RESTORE_QUEUE")
    dead_letter_queue: str = Field(..., validation_alias="DEAD_LETTER_QUEUE")
    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(',')
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
