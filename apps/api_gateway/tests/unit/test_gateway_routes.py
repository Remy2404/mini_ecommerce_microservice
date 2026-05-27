import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.api_gateway.app.infrastructure.http import proxy_client as proxy
from apps.api_gateway.app.infrastructure.security import wso2_client as auth
from apps.api_gateway.app.main import app
from packages.config.settings import settings
from packages.security.jwt import create_access_token


class FakeAsyncClient:
    calls: list[dict] = []
    response: httpx.Response = httpx.Response(200, json={"ok": True})

    def __init__(self, *args, **kwargs) -> None:
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def request(self, **kwargs):
        self.__class__.calls.append(kwargs)
        return self.__class__.response


def test_auth_category_and_payment_routes_proxy(monkeypatch) -> None:
    FakeAsyncClient.calls = []
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "auth_service_url", "http://auth-service")
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")
    monkeypatch.setattr(settings, "payment_service_url", "http://payment-service")

    with TestClient(app) as client:
        client.post("/api/v1/auth/register", json={"email": "a@example.com"})
        client.get("/api/v1/categories")
        client.get("/api/v1/payments/pay_123")

    assert FakeAsyncClient.calls[0]["url"] == "http://auth-service/auth/register"
    assert FakeAsyncClient.calls[1]["url"] == "http://product-service/categories"
    assert FakeAsyncClient.calls[2]["url"] == "http://payment-service/payments/pay_123"


def test_gateway_accepts_local_auth_service_jwt(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(settings, "jwt_secret_key", SecretStr("x" * 32))

    token = create_access_token(subject="user-123", roles=["customer"])
    payload = __import__("anyio").run(
        auth.validate_token,
        type("Credentials", (), {"credentials": token})(),
    )

    assert payload["sub"] == "user-123"
    assert payload["roles"] == ["customer"]
