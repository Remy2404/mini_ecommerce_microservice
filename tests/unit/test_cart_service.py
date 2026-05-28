from decimal import Decimal
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from packages.config.settings import settings
from apps.cart_service.app.application import services as cart_service
from apps.cart_service.app.infrastructure.clients import product_client
from apps.cart_service.app.main import app
from apps.cart_service.app.schemas import CartItemResponse, CartResponse

PRODUCT_ID = uuid4()


class FakeAsyncClient:
    calls: list[dict[str, str]] = []
    init_kwargs: list[dict] = []
    response: httpx.Response = httpx.Response(200)
    error: Exception | None = None

    def __init__(self, *args, **kwargs) -> None:
        self.__class__.init_kwargs.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def get(self, url: str) -> httpx.Response:
        self.__class__.calls.append({"url": url})
        if self.__class__.error is not None:
            raise self.__class__.error

        return self.__class__.response


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _product_response(
    *,
    product_id=PRODUCT_ID,
    name: str = "Trusted Product",
    price: str = "12.50",
) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "success": True,
            "message": "Product fetched successfully",
            "data": {
                "product_id": str(product_id),
                "name": name,
                "description": None,
                "price": price,
                "stock_quantity": 10,
                "category": "demo",
            },
        },
    )


def _reset_fake_http_client() -> None:
    FakeAsyncClient.calls = []
    FakeAsyncClient.init_kwargs = []
    FakeAsyncClient.response = _product_response()
    FakeAsyncClient.error = None


def _install_cart_fakes(
    monkeypatch,
    *,
    existing_cart: CartResponse | None = None,
) -> list[CartResponse]:
    saved_carts: list[CartResponse] = []

    monkeypatch.setattr(product_client.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")
    monkeypatch.setattr(settings, "gateway_request_timeout_seconds", 3.0)
    monkeypatch.setattr(
        cart_service,
        "get_cart",
        lambda user_id: (
            existing_cart
            or CartResponse(user_id=user_id, items=[], total_amount=Decimal("0"))
        ),
    )
    monkeypatch.setattr(cart_service, "save_cart", saved_carts.append)

    return saved_carts


def test_health_endpoint_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.cart_service_name}


def test_metrics_endpoint_returns_prometheus_data() -> None:
    with TestClient(app) as client:
        # Generate some traffic first
        client.get("/health")

        response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_request_total" in response.text


def test_add_cart_item_requires_only_user_product_and_quantity(monkeypatch) -> None:
    _reset_fake_http_client()
    saved_carts = _install_cart_fakes(monkeypatch)

    with TestClient(app) as client:
        response = client.post(
            "/cart/items",
            json={
                "user_id": "user_123",
                "product_id": str(PRODUCT_ID),
                "quantity": 2,
            },
        )

    assert response.status_code == 201
    assert FakeAsyncClient.calls == [
        {"url": f"http://product-service/products/{PRODUCT_ID}"}
    ]
    assert FakeAsyncClient.init_kwargs[0]["timeout"] == 3.0

    body = response.json()
    item = body["data"]["items"][0]
    assert item["name"] == "Trusted Product"
    assert item["quantity"] == 2
    assert _decimal(item["unit_price"]) == Decimal("12.50")
    assert _decimal(item["subtotal"]) == Decimal("25.00")
    assert _decimal(body["data"]["total_amount"]) == Decimal("25.00")
    assert saved_carts[0].items[0].unit_price == Decimal("12.50")


def test_add_cart_item_rejects_client_supplied_price_and_name(monkeypatch) -> None:
    _reset_fake_http_client()
    saved_carts = _install_cart_fakes(monkeypatch)

    with TestClient(app) as client:
        response = client.post(
            "/cart/items",
            json={
                "user_id": "user_123",
                "product_id": str(PRODUCT_ID),
                "name": "Fake Product",
                "quantity": 2,
                "unit_price": "0.01",
            },
        )

    assert response.status_code == 422
    assert FakeAsyncClient.calls == []
    assert saved_carts == []


def test_add_cart_item_returns_404_when_product_not_found(monkeypatch) -> None:
    _reset_fake_http_client()
    FakeAsyncClient.response = httpx.Response(
        404,
        json={"detail": "Product not found"},
    )
    saved_carts = _install_cart_fakes(monkeypatch)

    with TestClient(app) as client:
        response = client.post(
            "/cart/items",
            json={
                "user_id": "user_123",
                "product_id": str(PRODUCT_ID),
                "quantity": 1,
            },
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}
    assert saved_carts == []


def test_add_cart_item_returns_503_when_product_service_unavailable(
    monkeypatch,
) -> None:
    _reset_fake_http_client()
    FakeAsyncClient.error = httpx.ConnectError("connection failed")
    saved_carts = _install_cart_fakes(monkeypatch)

    with TestClient(app) as client:
        response = client.post(
            "/cart/items",
            json={
                "user_id": "user_123",
                "product_id": str(PRODUCT_ID),
                "quantity": 1,
            },
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Product service unavailable"}
    assert saved_carts == []


def test_existing_cart_item_is_repriced_from_trusted_product(monkeypatch) -> None:
    _reset_fake_http_client()
    FakeAsyncClient.response = _product_response(
        name="Trusted Product",
        price="8.25",
    )
    existing_cart = CartResponse(
        user_id="user_123",
        items=[
            CartItemResponse(
                product_id=PRODUCT_ID,
                name="Tampered Product",
                quantity=1,
                unit_price=Decimal("0.01"),
                subtotal=Decimal("0.01"),
            )
        ],
        total_amount=Decimal("0.01"),
    )
    saved_carts = _install_cart_fakes(monkeypatch, existing_cart=existing_cart)

    with TestClient(app) as client:
        response = client.post(
            "/cart/items",
            json={
                "user_id": "user_123",
                "product_id": str(PRODUCT_ID),
                "quantity": 2,
            },
        )

    assert response.status_code == 201
    item = response.json()["data"]["items"][0]
    assert item["name"] == "Trusted Product"
    assert item["quantity"] == 3
    assert _decimal(item["unit_price"]) == Decimal("8.25")
    assert _decimal(item["subtotal"]) == Decimal("24.75")
    assert _decimal(response.json()["data"]["total_amount"]) == Decimal("24.75")
    assert saved_carts[0].items[0].unit_price == Decimal("8.25")
