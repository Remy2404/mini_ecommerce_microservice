"""Security settings."""

from pydantic import Field


class SecuritySettings:
    jwt_algorithm: str = Field(..., validation_alias="JWT_ALGORITHM")
    cors_allowed_origins: str = Field(..., validation_alias="CORS_ALLOWED_ORIGINS")
    tls_enabled: bool = Field(..., validation_alias="TLS_ENABLED")
    cert_validation_enabled: bool = Field(..., validation_alias="CERT_VALIDATION_ENABLED")
    ca_cert_path: str = Field(..., validation_alias="CA_CERT_PATH")
    client_cert_path: str = Field(..., validation_alias="CLIENT_CERT_PATH")
    client_key_path: str = Field(..., validation_alias="CLIENT_KEY_PATH")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
