"""Database settings."""

from pydantic import Field


class DatabaseSettings:
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

    def service_database_url(self, database_name: str) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{database_name}"
        )

    @property
    def resolved_auth_database_url(self) -> str:
        return self.auth_database_url or self.service_database_url(self.auth_database_name)
