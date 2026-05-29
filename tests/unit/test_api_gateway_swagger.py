import json

import httpx
import pytest
from fastapi.testclient import TestClient

from apps.api_gateway.app.main import app
from apps.api_gateway.app.infrastructure.http import proxy_client as proxy
from packages.config.settings import settings
from packages.security import wso2_login
from packages.security.headers import AUTHENTICATED_USER_ID_HEADER


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
    monkeypatch.setattr(settings, "payment_service_url", "http://payment-service")


def _request_body_schema(openapi_schema: dict, path: str) -> dict:
    schema = openapi_schema["paths"][path]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    ref = schema.get("$ref")
    if ref is None:
        return schema

    schema_name = ref.rsplit("/", 1)[-1]
    return openapi_schema["components"]["schemas"][schema_name]


def test_openapi_includes_explicit_gateway_routes_and_hides_catch_all() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    paths = schema["paths"]

    assert "/api/v1/{service}{path}" not in paths
    assert "/api/v1/{service}/{path}" not in paths
    assert "/auth/login" not in paths
    assert "/internal/wso2/login" not in paths

    expected_routes = {
        ("/api/v1/auth/register", "post", "WSO2 Gateway"),
        ("/api/v1/auth/login", "post", "WSO2 Gateway"),
        ("/api/v1/auth/me", "get", "WSO2 Gateway"),
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
    }

    for path, method, tag in expected_routes:
        assert method in paths[path]
        assert paths[path][method]["tags"] == [tag]

    operation_tags = {
        tag
        for path_item in paths.values()
        for operation in path_item.values()
        for tag in operation.get("tags", [])
    }
    assert "WSO2 Gateway" in operation_tags
    assert "Auth Gateway" not in operation_tags
    assert "WSO2 Auth" not in operation_tags
    assert "/api/v1/auth/addresses" not in paths


def test_openapi_documents_auth_register_and_wso2_login_responses() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    register_operation = schema["paths"]["/api/v1/auth/register"]["post"]
    login_operation = schema["paths"]["/api/v1/auth/login"]["post"]

    assert "201" in register_operation["responses"]
    assert "503" in register_operation["responses"]
    assert "200" not in register_operation["responses"]
    assert (
        "Creates a WSO2 Identity Server user through SCIM2"
        in register_operation["description"]
    )

    login_success_ref = login_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    login_success_schema = schema["components"]["schemas"][
        login_success_ref.rsplit("/", 1)[-1]
    ]

    assert {"access_token", "token_type"} <= set(login_success_schema["properties"])
    assert "401" in login_operation["responses"]
    assert "503" in login_operation["responses"]
    assert "502" not in login_operation["responses"]
    assert "Use the WSO2 username" in login_operation["description"]


def test_openapi_documents_gateway_post_request_body_fields() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    expected_request_bodies = {
        "/api/v1/auth/register": (
            {"username", "email", "password", "given_name", "family_name"},
            {"username", "email", "password", "given_name", "family_name"},
        ),
        "/api/v1/auth/login": (
            {"username", "password", "scope"},
            {"username", "password"},
        ),
        "/api/v1/categories": (
            {"name", "description"},
            {"name"},
        ),
        "/api/v1/products": (
            {"name", "description", "price", "stock_quantity", "category"},
            {"name", "price", "stock_quantity", "category"},
        ),
        "/api/v1/cart/items": (
            {"product_id", "quantity"},
            {"product_id", "quantity"},
        ),
        "/api/v1/orders": (
            set(),
            set(),
        ),
    }

    for path, (properties, required) in expected_request_bodies.items():
        operation = schema["paths"][path]["post"]
        media_type = operation["requestBody"]["content"]["application/json"]
        request_schema = _request_body_schema(schema, path)

        assert operation["requestBody"]["required"] is True
        assert properties <= set(request_schema["properties"])
        assert required <= set(request_schema.get("required", []))
        assert "example" in media_type or "example" in request_schema


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

    monkeypatch.setattr(wso2_login.httpx, "AsyncClient", FakeWSO2AsyncClient)
    monkeypatch.setattr(settings, "wso2_token_url", "https://wso2.local/oauth2/token")
    monkeypatch.setattr(settings, "wso2_client_id", "local-client-id")
    monkeypatch.setattr(settings, "wso2_client_secret", "local-client-secret")
    monkeypatch.setattr(settings, "wso2_request_timeout_seconds", 7.5)
    monkeypatch.setattr(settings, "wso2_verify_ssl", False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
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


def test_wso2_login_preserves_special_characters_in_password(monkeypatch) -> None:
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

    monkeypatch.setattr(wso2_login.httpx, "AsyncClient", FakeWSO2AsyncClient)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "temporary$#Password!",
            },
        )

    assert response.status_code == 200
    assert FakeWSO2AsyncClient.calls[0]["data"]["password"] == "temporary$#Password!"


def test_wso2_login_invalid_credentials_return_safe_401(monkeypatch) -> None:
    FakeWSO2AsyncClient.calls = []
    FakeWSO2AsyncClient.init_kwargs = []
    FakeWSO2AsyncClient.response = httpx.Response(401, json={"error": "invalid_grant"})

    monkeypatch.setattr(wso2_login.httpx, "AsyncClient", FakeWSO2AsyncClient)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


def test_wso2_login_client_configuration_errors_return_safe_503(monkeypatch) -> None:
    FakeWSO2AsyncClient.calls = []
    FakeWSO2AsyncClient.init_kwargs = []
    FakeWSO2AsyncClient.response = httpx.Response(401, json={"error": "invalid_client"})

    monkeypatch.setattr(wso2_login.httpx, "AsyncClient", FakeWSO2AsyncClient)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}


def test_wso2_login_unknown_upstream_errors_return_safe_503(monkeypatch) -> None:
    FakeWSO2AsyncClient.calls = []
    FakeWSO2AsyncClient.init_kwargs = []
    FakeWSO2AsyncClient.response = httpx.Response(
        400,
        json={"error": "unexpected_wso2_error"},
    )

    monkeypatch.setattr(wso2_login.httpx, "AsyncClient", FakeWSO2AsyncClient)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}


def test_wso2_login_timeout_or_unavailable_returns_safe_503(monkeypatch) -> None:
    class RaisingAsyncClient(FakeWSO2AsyncClient):
        async def post(self, url: str, **kwargs) -> httpx.Response:
            raise httpx.ConnectTimeout("timeout")

    monkeypatch.setattr(wso2_login.httpx, "AsyncClient", RaisingAsyncClient)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong"},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}


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
        ("/api/v1/orders", b"{}", "http://order-service/orders"),
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
    if path in {"/api/v1/cart/items", "/api/v1/orders"}:
        assert json.loads(call["content"]) == json.loads(payload)
        assert forwarded_headers[AUTHENTICATED_USER_ID_HEADER] == "local-demo"
    else:
        assert call["content"] == payload
    assert forwarded_headers["authorization"] == "Bearer test-token"
    assert forwarded_headers["x-request-id"] == "request-123"
    assert (
        forwarded_headers["traceparent"]
        == "00-00000000000000000000000000000000-0000000000000000-01"
    )


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/api/v1/cart/items", b'{"user_id":"attacker","product_id":"product_123"}'),
        ("/api/v1/orders", b'{"user_id":"attacker"}'),
    ],
)
def test_user_owned_post_routes_reject_client_supplied_user_id(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    payload: bytes,
) -> None:
    _configure_gateway(monkeypatch)

    with TestClient(app) as client:
        response = client.post(path, content=payload)

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}
    assert FakeAsyncClient.calls == []
