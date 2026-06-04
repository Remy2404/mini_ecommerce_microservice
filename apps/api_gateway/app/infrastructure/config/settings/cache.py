"""Cache settings."""

from pydantic import Field


class CacheSettings:
    valkey_host: str = Field(..., validation_alias="VALKEY_HOST")
    valkey_port: int = Field(..., validation_alias="VALKEY_PORT")
    valkey_password: str = Field("", validation_alias="VALKEY_PASSWORD")
    valkey_url: str = Field(..., validation_alias="VALKEY_URL")

    product_cache_ttl_seconds: int = Field(..., validation_alias="PRODUCT_CACHE_TTL_SECONDS")
    cart_cache_ttl_seconds: int = Field(..., validation_alias="CART_CACHE_TTL_SECONDS")
    rate_limit_ttl_seconds: int = Field(..., validation_alias="RATE_LIMIT_TTL_SECONDS")
