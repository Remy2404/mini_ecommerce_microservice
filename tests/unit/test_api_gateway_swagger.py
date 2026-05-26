import httpx
import pytest
from fastapi.testclient import TestClient

from packages.config.settings import settings
from services.api_gateway.app.main import app
from services.api_gateway.app.routers import proxy


class FakeAsyncClient:
    calls: list[dict] = []
    init_kwargs: list[dict] = []
    response: httpx.Response = httpx.Response(200, json={"ok": True})

    def __init__(self, *args, **kwargs) -> None:
        self.__class__.init_kwargs.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def request(self, **kwargs) -> httpx.Response:
        self.__class__.calls.append(kwargs)
        return self.__class__.response


class FakeWSO2AsyncClient:
    calls: list[dict] = []
    init_kwargs: list[dict] = []
    response: httpx.Response = httpx.Response(
        200,
        json={
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    def __init__(self, *args, **kwargs) -> None:
        self.__class__.init_kwargs.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, url: str, **kwargs) -> httpx.Response:
        self.__class__.calls.append({"url": url, **kwargs})
        return self.__class__.response


def _reset_fake_http_client() -> None:
    FakeAsyncClient.calls = []
    FakeAsyncClient.init_kwargs = []
    FakeAsyncClient.response = httpx.Response(200, json={"ok": True})


def _configure_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_fake_http_client()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")
    monkeypatch.setattr(settings, "cart_service_url", "http://cart-service")
    monkeypatch.setattr(settings, "order_service_url", "http://order-service")


def test_openapi_includes_explicit_gateway_routes_and_hides_catch_all() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    paths = schema["paths"]

    assert "/api/v1/{service}{path}" not in paths
    assert "/api/v1/{service}/{path}" not in paths

    expected_routes = {
        ("/api/v1/products", "get", "Product Gateway"),
        ("/api/v1/products", "post", "Product Gateway"),
        ("/api/v1/products/{product_id}", "get", "Product Gateway"),
        ("/api/v1/cart/{user_id}", "get", "Cart Gateway"),
        ("/api/v1/cart/items", "post", "Cart Gateway"),
        ("/api/v1/cart/{user_id}/items/{product_id}", "delete", "Cart Gateway"),
        ("/api/v1/cart/{user_id}", "delete", "Cart Gateway"),
        ("/api/v1/orders", "get", "Order Gateway"),
        ("/api/v1/orders", "post", "Order Gateway"),
        ("/api/v1/orders/{order_id}", "get", "Order Gateway"),
        ("/auth/login", "post", "WSO2 Auth"),
    }

    for path, method, tag in expected_routes:
        assert method in paths[path]
        assert paths[path][method]["tags"] == [tag]


def test_wso2_login_uses_password_grant(monkeypatch) -> None:
    FakeWSO2AsyncClient.calls = []
    FakeWSO2AsyncClient.init_kwargs = []
    FakeWSO2AsyncClient.response = httpx.Response(
        200,
        json={
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    from services.api_gateway.app.routers import auth_routes

    monkeypatch.setattr(auth_routes.httpx, "AsyncClient", FakeWSO2AsyncClient)
    monkeypatch.setattr(settings, "wso2_token_url", "https://wso2.local/oauth2/token")
    monkeypatch.setattr(settings, "wso2_client_id", "local-client-id")
    monkeypatch.setattr(settings, "wso2_client_secret", "local-client-secret")
    monkeypatch.setattr(settings, "wso2_request_timeout_seconds", 7.5)
    monkeypatch.setattr(settings, "wso2_verify_ssl", False)

    with TestClient(app) as client:
        response = client.post(
            "/auth/login",
            json={
                "username": "admin",
                "password": "admin",
                "scope": "openid profile",
            },
        )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access-token"

    call = FakeWSO2AsyncClient.calls[0]
    assert call["url"] == "https://wso2.local/oauth2/token"
    assert call["data"] == {
        "grant_type": "password",
        "username": "admin",
        "password": "admin",
        "scope": "openid profile",
        "client_id": "local-client-id",
        "client_secret": "local-client-secret",
    }
    assert call["headers"] == {"Content-Type": "application/x-www-form-urlencoded"}
    assert FakeWSO2AsyncClient.init_kwargs == [{"timeout": 7.5, "verify": False}]


def test_wso2_login_invalid_credentials_return_safe_401(monkeypatch) -> None:
    FakeWSO2AsyncClient.calls = []
    FakeWSO2AsyncClient.init_kwargs = []
    FakeWSO2AsyncClient.response = httpx.Response(401, json={"error": "invalid_grant"})

    from services.api_gateway.app.routers import auth_routes

    monkeypatch.setattr(auth_routes.httpx, "AsyncClient", FakeWSO2AsyncClient)

    with TestClient(app) as client:
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrong"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


@pytest.mark.parametrize(
    ("method", "path", "expected_url"),
    [
        ("GET", "/api/v1/products", "http://product-service/products"),
        (
            "GET",
            "/api/v1/products/product_123",
            "http://product-service/products/product_123",
        ),
        ("GET", "/api/v1/cart/user_123", "http://cart-service/cart/user_123"),
        (
            "DELETE",
            "/api/v1/cart/user_123/items/product_123",
            "http://cart-service/cart/user_123/items/product_123",
        ),
        ("DELETE", "/api/v1/cart/user_123", "http://cart-service/cart/user_123"),
        ("GET", "/api/v1/orders", "http://order-service/orders"),
        ("GET", "/api/v1/orders/order_123", "http://order-service/orders/order_123"),
    ],
)
def test_explicit_get_and_delete_routes_proxy_correctly(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path: str,
    expected_url: str,
) -> None:
    _configure_gateway(monkeypatch)

    with TestClient(app) as client:
        response = client.request(method, path)

    assert response.status_code == 200
    assert FakeAsyncClient.calls[0]["method"] == method
    assert FakeAsyncClient.calls[0]["url"] == expected_url


@pytest.mark.parametrize(
    ("path", "payload", "expected_url"),
    [
        ("/api/v1/products", b'{"name":"Hat"}', "http://product-service/products"),
        (
            "/api/v1/cart/items",
            b'{"product_id":"product_123"}',
            "http://cart-service/cart/items",
        ),
        ("/api/v1/orders", b'{"user_id":"user_123"}', "http://order-service/orders"),
    ],
)
def test_explicit_post_routes_forward_raw_body_and_headers(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    payload: bytes,
    expected_url: str,
) -> None:
    _configure_gateway(monkeypatch)

    with TestClient(app) as client:
        response = client.post(
            path,
            content=payload,
            headers={
                "Authorization": "Bearer test-token",
                "X-Request-ID": "request-123",
                "traceparent": "00-00000000000000000000000000000000-0000000000000000-01",
            },
        )

    assert response.status_code == 200

    call = FakeAsyncClient.calls[0]
    forwarded_headers = httpx.Headers(call["headers"])
    assert call["method"] == "POST"
    assert call["url"] == expected_url
    assert call["content"] == payload
    assert forwarded_headers["authorization"] == "Bearer test-token"
    assert forwarded_headers["x-request-id"] == "request-123"
    assert (
        forwarded_headers["traceparent"]
        == "00-00000000000000000000000000000000-0000000000000000-01"
    )
