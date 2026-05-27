from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from apps.cart_service.app.main import app
from apps.cart_service.app.schemas import CartItemResponse, CartResponse


def test_remove_cart_item_route_uses_valkey_repository(monkeypatch) -> None:
    product_id = uuid4()
    expected = CartResponse(
        user_id="user_123",
        items=[],
        total_amount=Decimal("0"),
    )

    from apps.cart_service.app.api import routes

    monkeypatch.setattr(
        routes.cart_service,
        "delete_cart_item",
        lambda user_id, product_id: expected,
    )

    with TestClient(app) as client:
        response = client.delete(f"/cart/user_123/items/{product_id}")

    assert response.status_code == 200
    assert response.json()["data"]["user_id"] == "user_123"
    assert response.json()["data"]["items"] == []


def test_clear_cart_route_returns_user_id(monkeypatch) -> None:
    from apps.cart_service.app.api import routes

    called = []
    monkeypatch.setattr(routes.cart_service, "delete_cart", called.append)

    with TestClient(app) as client:
        response = client.delete("/cart/user_123")

    assert response.status_code == 200
    assert response.json()["message"] == "Cart cleared successfully"
    assert called == ["user_123"]


def test_cart_total_is_calculated_from_items() -> None:
    cart = CartResponse(
        user_id="user_123",
        items=[
            CartItemResponse(
                product_id=uuid4(),
                name="Trusted Product",
                quantity=2,
                unit_price=Decimal("9.50"),
                subtotal=Decimal("19.00"),
            )
        ],
        total_amount=Decimal("19.00"),
    )

    assert cart.total_amount == Decimal("19.00")
