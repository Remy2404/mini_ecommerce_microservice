from uuid import UUID

import httpx
from fastapi.testclient import TestClient

from apps.api_gateway.app.api.dependencies import (
    validate_token as gateway_validate_token,
)
from packages.config.settings import settings
from apps.api_gateway.app.main import app
from apps.api_gateway.app.infrastructure.http import proxy_client as proxy


class FakeAsyncClient:
    calls: list[dict] = []
    init_kwargs: list[dict] = []
    response: httpx.Response = httpx.Response(200, json={"ok": True})
    error: Exception | None = None

    def __init__(self, *args, **kwargs) -> None:
        self.__class__.init_kwargs.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def request(self, **kwargs) -> httpx.Response:
        self.__class__.calls.append(kwargs)
        if self.__class__.error is not None:
            raise self.__class__.error

        return self.__class__.response


def _headers(headers: dict[str, str]) -> httpx.Headers:
    return httpx.Headers(headers)


def _reset_fake_http_client() -> None:
    FakeAsyncClient.calls = []
    FakeAsyncClient.init_kwargs = []
    FakeAsyncClient.response = httpx.Response(200, json={"ok": True})
    FakeAsyncClient.error = None


def test_health_endpoint_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": settings.api_gateway_service_name,
    }


def test_metrics_endpoint_returns_prometheus_data() -> None:
    with TestClient(app) as client:
        response = client.get("/metrics/")
        alternate_response = client.get("/metrics")

    assert response.status_code == 200
    assert alternate_response.status_code == 200
    assert "http_request_total" in response.text


def test_product_route_proxies_correctly(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/products",
            headers={
                "Authorization": "Bearer test-token",
                "X-Request-ID": "request-123",
                "traceparent": "00-00000000000000000000000000000000-0000000000000000-01",
            },
        )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "request-123"

    call = FakeAsyncClient.calls[0]
    forwarded_headers = _headers(call["headers"])
    assert call["method"] == "GET"
    assert call["url"] == "http://product-service/products"
    assert forwarded_headers["authorization"] == "Bearer test-token"
    assert forwarded_headers["x-request-id"] == "request-123"
    assert (
        forwarded_headers["traceparent"]
        == "00-00000000000000000000000000000000-0000000000000000-01"
    )
    assert "host" not in forwarded_headers
    assert (
        FakeAsyncClient.init_kwargs[0]["timeout"]
        == settings.gateway_request_timeout_seconds
    )


def test_cart_route_proxies_correctly(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "cart_service_url", "http://cart-service")

    with TestClient(app) as client:
        response = client.get("/api/v1/cart/user_123")

    assert response.status_code == 200
    assert FakeAsyncClient.calls[0]["url"] == "http://cart-service/cart/user_123"


def test_order_route_proxies_correctly(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "order_service_url", "http://order-service")

    with TestClient(app) as client:
        response = client.get("/api/v1/orders")

    assert response.status_code == 200
    assert FakeAsyncClient.calls[0]["url"] == "http://order-service/orders"


def test_unknown_service_returns_safe_404(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)

    with TestClient(app) as client:
        response = client.get("/api/v1/unknown/path")

    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown service"}
    assert FakeAsyncClient.calls == []


def test_missing_request_id_is_generated(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")

    with TestClient(app) as client:
        response = client.get("/api/v1/products")

    request_id = response.headers["x-request-id"]
    UUID(request_id)
    assert _headers(FakeAsyncClient.calls[0]["headers"])["x-request-id"] == request_id


def test_existing_request_id_is_preserved(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/products",
            headers={"X-Request-ID": "existing-request-id"},
        )

    assert response.headers["x-request-id"] == "existing-request-id"
    assert (
        _headers(FakeAsyncClient.calls[0]["headers"])["x-request-id"]
        == "existing-request-id"
    )


def test_auth_disabled_mode_allows_local_request(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")

    with TestClient(app) as client:
        response = client.get("/api/v1/products")

    assert response.status_code == 200
    assert len(FakeAsyncClient.calls) == 1


def test_owned_routes_inject_user_id_from_token_sub(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "cart_service_url", "http://cart-service")
    monkeypatch.setattr(settings, "order_service_url", "http://order-service")
    monkeypatch.setattr(settings, "payment_service_url", "http://payment-service")

    app.dependency_overrides[gateway_validate_token] = lambda: {
        "sub": "user-from-sub",
        "roles": ["customer"],
    }
    try:
        with TestClient(app) as client:
            client.post(
                "/api/v1/cart/items",
                json={"product_id": "product_123", "quantity": 1},
            )
            client.get("/api/v1/orders")
            client.get("/api/v1/payments/pay_123")
    finally:
        app.dependency_overrides.clear()

    forwarded_headers = [
        httpx.Headers(call["headers"]) for call in FakeAsyncClient.calls
    ]
    assert forwarded_headers[0]["x-authenticated-user-id"] == "user-from-sub"
    assert forwarded_headers[1]["x-authenticated-user-id"] == "user-from-sub"
    assert forwarded_headers[2]["x-authenticated-user-id"] == "user-from-sub"


def test_owned_post_routes_reject_client_supplied_user_id(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "cart_service_url", "http://cart-service")
    monkeypatch.setattr(settings, "order_service_url", "http://order-service")

    app.dependency_overrides[gateway_validate_token] = lambda: {
        "sub": "user-from-sub",
        "roles": ["customer"],
    }
    try:
        with TestClient(app) as client:
            cart_response = client.post(
                "/api/v1/cart/items",
                json={
                    "user_id": "evil-user",
                    "product_id": "product_123",
                    "quantity": 1,
                },
            )
            order_response = client.post(
                "/api/v1/orders",
                json={"user_id": "evil-user"},
            )
    finally:
        app.dependency_overrides.clear()

    assert cart_response.status_code == 403
    assert cart_response.json() == {"detail": "Forbidden"}
    assert order_response.status_code == 403
    assert order_response.json() == {"detail": "Forbidden"}
    assert FakeAsyncClient.calls == []


def test_downstream_connect_error_maps_to_503(monkeypatch) -> None:
    _reset_fake_http_client()
    FakeAsyncClient.error = httpx.ConnectError("connection failed")
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")

    with TestClient(app) as client:
        response = client.get("/api/v1/products")

    assert response.status_code == 503
    assert response.json() == {"detail": "Downstream service unavailable"}


def test_downstream_400_and_404_statuses_are_preserved(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")

    with TestClient(app) as client:
        FakeAsyncClient.response = httpx.Response(400, json={"detail": "Bad request"})
        bad_request_response = client.get("/api/v1/products")

        FakeAsyncClient.response = httpx.Response(404, json={"detail": "Not found"})
        not_found_response = client.get("/api/v1/products/missing")

    assert bad_request_response.status_code == 400
    assert not_found_response.status_code == 404


def test_downstream_5xx_uses_safe_body(monkeypatch) -> None:
    _reset_fake_http_client()
    FakeAsyncClient.response = httpx.Response(
        503,
        text="database password leaked in stack trace",
    )
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")

    with TestClient(app) as client:
        response = client.get("/api/v1/products")

    assert response.status_code == 503
    assert response.json() == {"detail": "Downstream service error"}
    assert "password" not in response.text


def test_downstream_5xx_preserves_allowlisted_safe_auth_error(monkeypatch) -> None:
    _reset_fake_http_client()
    FakeAsyncClient.response = httpx.Response(
        503,
        json={"detail": "WSO2 registration configuration error"},
    )
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "auth_service_url", "http://auth-service")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "john.doe",
                "email": "ramy@example.com",
                "password": "StrongPass@123",
                "first_name": "John",
                "last_name": "Doe",
            },
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "WSO2 registration configuration error"}


def test_no_open_proxy_behavior(monkeypatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")

    with TestClient(app) as client:
        response = client.get("/api/v1/products/http://evil.example/resource")

    assert response.status_code == 200
    assert FakeAsyncClient.calls[0]["url"] == (
        "http://product-service/products/http://evil.example/resource"
    )
