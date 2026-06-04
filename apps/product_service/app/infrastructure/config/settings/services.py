"""Service discovery and endpoint settings."""

from pydantic import Field


class ServiceSettings:
    api_gateway_service_name: str = Field(
        ..., validation_alias="API_GATEWAY_SERVICE_NAME"
    )
    auth_service_name: str = Field("auth-service", validation_alias="AUTH_SERVICE_NAME")
    product_service_name: str = Field(..., validation_alias="PRODUCT_SERVICE_NAME")
    cart_service_name: str = Field(..., validation_alias="CART_SERVICE_NAME")
    order_service_name: str = Field(..., validation_alias="ORDER_SERVICE_NAME")
    payment_service_name: str = Field(..., validation_alias="PAYMENT_SERVICE_NAME")

    api_gateway_port: int = Field(..., validation_alias="API_GATEWAY_PORT")
    auth_service_port: int = Field(8005, validation_alias="AUTH_SERVICE_PORT")
    product_service_port: int = Field(..., validation_alias="PRODUCT_SERVICE_PORT")
    cart_service_port: int = Field(..., validation_alias="CART_SERVICE_PORT")
    order_service_port: int = Field(..., validation_alias="ORDER_SERVICE_PORT")
    payment_service_port: int = Field(..., validation_alias="PAYMENT_SERVICE_PORT")

    product_service_url: str = Field(..., validation_alias="PRODUCT_SERVICE_URL")
    auth_service_url: str = Field(
        "http://localhost:8005",
        validation_alias="AUTH_SERVICE_URL",
    )
    cart_service_url: str = Field(..., validation_alias="CART_SERVICE_URL")
    order_service_url: str = Field(..., validation_alias="ORDER_SERVICE_URL")
    payment_service_url: str = Field(..., validation_alias="PAYMENT_SERVICE_URL")

    @property
    def api_gateway(self) -> str:
        """Backward-compatible alias for existing service-name references."""
        return self.api_gateway_service_name
