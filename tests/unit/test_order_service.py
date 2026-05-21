from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from packages.config.settings import settings
from services.order_service.main import app


def test_health_endpoint_returns_ok() -> None:
    with patch("services.order_service.main.broker.connect", new=AsyncMock()), patch(
        "services.order_service.main.broker.close",
        new=AsyncMock(),
    ):
        with TestClient(app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.order_service_name}


def test_create_order_endpoint_returns_created_order() -> None:
    with patch("services.order_service.main.broker.connect", new=AsyncMock()), patch(
        "services.order_service.main.broker.close",
        new=AsyncMock(),
    ), patch(
        "services.order_service.main.broker.publish",
        new=AsyncMock(),
    ) as publish_mock:
        with TestClient(app) as client:
            response = client.post("/orders")

    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Order created successfully"
    assert body["data"]["order_id"]
    assert body["data"]["status"] == "PENDING"
    publish_mock.assert_awaited_once()
