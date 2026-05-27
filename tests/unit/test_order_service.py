from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from packages.config.settings import settings
from app.services.order_service.main import app


def test_health_endpoint_returns_ok() -> None:
    with (
        patch("services.order_service.main.broker.connect", new=AsyncMock()),
        patch(
            "services.order_service.main.broker.close",
            new=AsyncMock(),
        ),
    ):
        with TestClient(app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.order_service_name}


def test_create_order_endpoint_returns_created_order() -> None:
    from app.services.order_service.cart_reader import CartSnapshot

    with (
        patch("services.order_service.main.broker.connect", new=AsyncMock()),
        patch(
            "services.order_service.main.broker.close",
            new=AsyncMock(),
        ),
        patch(
            "services.order_service.router.broker.publish",
            new=AsyncMock(),
        ) as publish_mock,
        patch(
            "services.order_service.router.get_cart_snapshot",
            return_value=CartSnapshot(
                cart_id="cart_user_123",
                total_amount=Decimal("150.00"),
                items=[],
            ),
        ),
        patch(
            "services.order_service.router.save_order_status",
            new=AsyncMock(),
        ),
        patch(
            "services.order_service.router.save_order",
            new=AsyncMock(),
        ) as save_order_mock,
    ):
        with TestClient(app) as client:
            response = client.post("/orders", json={"user_id": "user_123"})

    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Order created successfully"
    assert body["data"]["order_id"]
    assert body["data"]["status"] == "PENDING"
    publish_mock.assert_awaited_once()
    save_order_mock.assert_awaited_once()


@patch("services.order_service.consumers.save_order_status", new_callable=AsyncMock)
@patch("services.order_service.consumers.get_valkey_client")
@patch("services.order_service.consumers.setup_logging")
@patch("services.order_service.consumers.setup_tracing")
def test_handle_payment_success_clears_cart(
    mock_setup_tracing, mock_setup_logging, mock_valkey, mock_save_status
) -> None:
    from packages.contracts.events import PaymentSuccessEvent, PaymentSuccessPayload
    from app.services.order_service.consumers import handle_payment_result
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

    # Run the async consumer function in the event loop
    asyncio.run(handle_payment_result(event))

    mock_save_status.assert_awaited_once_with(
        order_id=str(event.payload.order_id),
        status="CONFIRMED",
    )
    mock_client.delete.assert_called_once_with("cart:user_123")


def test_create_order_cart_not_found() -> None:
    from app.services.order_service.cart_reader import CartNotFoundError

    with (
        patch("services.order_service.main.broker.connect", new=AsyncMock()),
        patch(
            "services.order_service.main.broker.close",
            new=AsyncMock(),
        ),
        patch(
            "services.order_service.router.get_cart_snapshot",
            side_effect=CartNotFoundError("Cart not found"),
        ),
    ):
        with TestClient(app) as client:
            response = client.post("/orders", json={"user_id": "user_123"})

    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Cart not found"


def test_create_order_cart_empty() -> None:
    from app.services.order_service.cart_reader import EmptyCartError

    with (
        patch("services.order_service.main.broker.connect", new=AsyncMock()),
        patch(
            "services.order_service.main.broker.close",
            new=AsyncMock(),
        ),
        patch(
            "services.order_service.router.get_cart_snapshot",
            side_effect=EmptyCartError("Cart is empty"),
        ),
    ):
        with TestClient(app) as client:
            response = client.post("/orders", json={"user_id": "user_123"})

    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Cart is empty"


def test_get_order_success() -> None:
    with (
        patch("services.order_service.main.broker.connect", new=AsyncMock()),
        patch(
            "services.order_service.main.broker.close",
            new=AsyncMock(),
        ),
        patch(
            "services.order_service.router.get_order_status",
            new=AsyncMock(return_value="PENDING"),
        ),
    ):
        with TestClient(app) as client:
            response = client.get("/orders/order_123")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["order_id"] == "order_123"
    assert body["data"]["status"] == "PENDING"


def test_get_order_not_found() -> None:
    with (
        patch("services.order_service.main.broker.connect", new=AsyncMock()),
        patch(
            "services.order_service.main.broker.close",
            new=AsyncMock(),
        ),
        patch(
            "services.order_service.router.get_order_status",
            new=AsyncMock(return_value=None),
        ),
    ):
        with TestClient(app) as client:
            response = client.get("/orders/order_123")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Order not found"


def test_list_orders() -> None:
    with (
        patch("services.order_service.main.broker.connect", new=AsyncMock()),
        patch(
            "services.order_service.main.broker.close",
            new=AsyncMock(),
        ),
        patch(
            "services.order_service.router.get_all_orders",
            new=AsyncMock(
                return_value={"order_123": "PENDING", "order_456": "CONFIRMED"}
            ),
        ),
    ):
        with TestClient(app) as client:
            response = client.get("/orders")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {"order_123": "PENDING", "order_456": "CONFIRMED"}


def test_metrics_endpoint_returns_prometheus_data() -> None:
    with (
        patch("services.order_service.main.broker.connect", new=AsyncMock()),
        patch(
            "services.order_service.main.broker.close",
            new=AsyncMock(),
        ),
    ):
        with TestClient(app) as client:
            # Generate some traffic first
            client.get("/health")

            response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_request_total" in response.text
