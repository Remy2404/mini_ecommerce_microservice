"""Gateway and transport security settings."""

from pydantic import Field


class SecuritySettings:
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

    jwt_algorithm: str = Field(..., validation_alias="JWT_ALGORITHM")
    cors_allowed_origins: str = Field(..., validation_alias="CORS_ALLOWED_ORIGINS")
    tls_enabled: bool = Field(..., validation_alias="TLS_ENABLED")
    cert_validation_enabled: bool = Field(
        ..., validation_alias="CERT_VALIDATION_ENABLED"
    )
    ca_cert_path: str = Field(..., validation_alias="CA_CERT_PATH")
    client_cert_path: str = Field(..., validation_alias="CLIENT_CERT_PATH")
    client_key_path: str = Field(..., validation_alias="CLIENT_KEY_PATH")

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]
