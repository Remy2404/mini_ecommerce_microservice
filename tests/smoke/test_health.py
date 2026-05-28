"""Smoke tests for in-process service health endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from apps.api_gateway.app.main import app as gateway_app
from apps.auth_service.app.main import app as auth_app
from apps.cart_service.app.main import app as cart_app
from apps.order_service.app.main import app as order_app
from apps.payment_service.app.main import app as payment_app
from apps.product_service.app.main import app as product_app


def test_core_http_services_expose_health_endpoints() -> None:
    service_apps = [
        ("api-gateway", gateway_app),
        ("auth-service", auth_app),
        ("product-service", product_app),
        ("cart-service", cart_app),
        ("payment-service", payment_app),
    ]

    for service_name, service_app in service_apps:
        with TestClient(service_app) as client:
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["service"] == service_name


def test_order_service_health_endpoint_without_real_broker_connection() -> None:
    with (
        patch("apps.order_service.app.main.broker.connect", new=AsyncMock()),
        patch("apps.order_service.app.main.broker.close", new=AsyncMock()),
    ):
        with TestClient(order_app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "order-service"
