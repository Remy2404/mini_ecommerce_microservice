from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from apps.order_service.app.application import services as order_services
from apps.order_service.app.main import app
from packages.config.settings import settings
from packages.security.headers import AUTHENTICATED_USER_ID_HEADER

OWNER_HEADERS = {AUTHENTICATED_USER_ID_HEADER: "user_123"}


def test_health_endpoint_returns_ok() -> None:
    with (
        patch("apps.order_service.app.main.broker.connect", new=AsyncMock()),
        patch(
            "apps.order_service.app.main.broker.close",
            new=AsyncMock(),
        ),
    ):
        with TestClient(app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.order_service_name}


def test_create_order_endpoint_returns_created_order() -> None:
    from apps.order_service.app.infrastructure.clients.cart_client import CartSnapshot

    with (
        patch("apps.order_service.app.main.broker.connect", new=AsyncMock()),
        patch(
            "apps.order_service.app.main.broker.close",
            new=AsyncMock(),
        ),
        patch(
            "apps.order_service.app.application.services.publish_pending_order_events",
            new=AsyncMock(),
        ) as publish_pending_mock,
        patch.object(
            order_services,
            "get_cart_snapshot",
            return_value=CartSnapshot(
                cart_id="cart_user_123",
                total_amount=Decimal("150.00"),
                items=[],
            ),
        ),
        patch.object(
            order_services,
            "save_order_with_outbox",
            new=AsyncMock(),
        ) as save_order_with_outbox_mock,
    ):
        with TestClient(app) as client:
            response = client.post("/orders", json={}, headers=OWNER_HEADERS)

    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Order created successfully"
    assert body["data"]["order_id"]
    assert body["data"]["status"] == "PENDING"
    publish_pending_mock.assert_awaited_once()
    save_order_with_outbox_mock.assert_awaited_once()


@patch("apps.order_service.app.infrastructure.messaging.payment_result_consumer.apply_payment_result_once", new_callable=AsyncMock)
@patch("apps.order_service.app.infrastructure.messaging.payment_result_consumer.get_valkey_client")
@patch("apps.order_service.app.infrastructure.messaging.payment_result_consumer.setup_logging")
@patch("apps.order_service.app.infrastructure.messaging.payment_result_consumer.setup_tracing")
def test_handle_payment_success_clears_cart(
    mock_setup_tracing, mock_setup_logging, mock_valkey, mock_apply_result
) -> None:
    from packages.contracts.events import PaymentSuccessEvent, PaymentSuccessPayload
    from apps.order_service.app.infrastructure.messaging.payment_result_consumer import handle_payment_result
    import asyncio

    event = PaymentSuccessEvent(
        payload=PaymentSuccessPayload(
            payment_id=uuid4(),
            order_id=uuid4(),
            user_id="user_123",
            amount=Decimal("150.00"),
        )
    )

    mock_client = mock_valkey.return_value
    mock_apply_result.return_value = True

    # Run the async consumer function in the event loop
    asyncio.run(handle_payment_result(event))

    mock_apply_result.assert_awaited_once_with(
        event_id=event.event_id,
        event_type=event.event_type,
        order_id=event.payload.order_id,
        status="CONFIRMED",
    )
    mock_client.delete.assert_called_once_with("cart:user_123")


def test_create_order_cart_not_found() -> None:
    from apps.order_service.app.infrastructure.clients.cart_client import CartNotFoundError

    with (
        patch("apps.order_service.app.main.broker.connect", new=AsyncMock()),
        patch(
            "apps.order_service.app.main.broker.close",
            new=AsyncMock(),
        ),
        patch.object(
            order_services,
            "get_cart_snapshot",
            side_effect=CartNotFoundError("Cart not found"),
        ),
    ):
        with TestClient(app) as client:
            response = client.post("/orders", json={}, headers=OWNER_HEADERS)

    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Cart not found"


def test_create_order_cart_empty() -> None:
    from apps.order_service.app.infrastructure.clients.cart_client import EmptyCartError

    with (
        patch("apps.order_service.app.main.broker.connect", new=AsyncMock()),
        patch(
            "apps.order_service.app.main.broker.close",
            new=AsyncMock(),
        ),
        patch.object(
            order_services,
            "get_cart_snapshot",
            side_effect=EmptyCartError("Cart is empty"),
        ),
    ):
        with TestClient(app) as client:
            response = client.post("/orders", json={}, headers=OWNER_HEADERS)

    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Cart is empty"


def test_get_order_success() -> None:
    with (
        patch("apps.order_service.app.main.broker.connect", new=AsyncMock()),
        patch(
            "apps.order_service.app.main.broker.close",
            new=AsyncMock(),
        ),
        patch(
            "apps.order_service.app.api.routes.get_order_status",
            new=AsyncMock(return_value="PENDING"),
        ),
    ):
        with TestClient(app) as client:
            response = client.get("/orders/order_123", headers=OWNER_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["order_id"] == "order_123"
    assert body["data"]["status"] == "PENDING"


def test_get_order_not_found() -> None:
    with (
        patch("apps.order_service.app.main.broker.connect", new=AsyncMock()),
        patch(
            "apps.order_service.app.main.broker.close",
            new=AsyncMock(),
        ),
        patch(
            "apps.order_service.app.api.routes.get_order_status",
            new=AsyncMock(return_value=None),
        ),
    ):
        with TestClient(app) as client:
            response = client.get("/orders/order_123", headers=OWNER_HEADERS)

    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Order not found"


def test_list_orders() -> None:
    with (
        patch("apps.order_service.app.main.broker.connect", new=AsyncMock()),
        patch(
            "apps.order_service.app.main.broker.close",
            new=AsyncMock(),
        ),
        patch(
            "apps.order_service.app.api.routes.get_all_orders",
            new=AsyncMock(
                return_value={"order_123": "PENDING", "order_456": "CONFIRMED"}
            ),
        ),
    ):
        with TestClient(app) as client:
            response = client.get("/orders", headers=OWNER_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {"order_123": "PENDING", "order_456": "CONFIRMED"}


def test_metrics_endpoint_returns_prometheus_data() -> None:
    with (
        patch("apps.order_service.app.main.broker.connect", new=AsyncMock()),
        patch(
            "apps.order_service.app.main.broker.close",
            new=AsyncMock(),
        ),
    ):
        with TestClient(app) as client:
            # Generate some traffic first
            client.get("/health")

            response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_request_total" in response.text
