from datetime import timedelta

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.api_gateway.app.infrastructure.cache import rate_limit_store
from apps.api_gateway.app.infrastructure.http import proxy_client
from apps.api_gateway.app.main import app as gateway_app
from apps.cart_service.app.main import app as cart_app
from packages.config.settings import settings
from packages.security.jwt import create_access_token


class FakeAsyncClient:
    response: httpx.Response = httpx.Response(200, json={"ok": True})

    def __init__(self, *args, **kwargs) -> None:
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def request(self, **kwargs):
        return self.response


class FakeRateLimitClient:
    def __init__(self) -> None:
        self.count = 0

    async def incr(self, key: str) -> int:
        self.count += 1
        return self.count

    async def expire(self, key: str, ttl_seconds: int) -> None:
        return None


def test_gateway_rejects_missing_auth(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    with TestClient(gateway_app) as client:
        response = client.get("/api/v1/products")

    assert response.status_code == 401


def test_gateway_rejects_invalid_local_jwt(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(settings, "jwt_secret_key", SecretStr("x" * 32))

    with TestClient(gateway_app) as client:
        response = client.get(
            "/api/v1/products",
            headers={"Authorization": "Bearer invalid.token.value"},
        )

    assert response.status_code == 401


def test_gateway_rejects_expired_local_jwt(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(settings, "jwt_secret_key", SecretStr("x" * 32))
    token = create_access_token(
        subject="user_123",
        expires_delta=timedelta(seconds=-1),
    )

    with TestClient(gateway_app) as client:
        response = client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401


def test_gateway_blocks_cart_idor(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "jwt_secret_key", SecretStr("x" * 32))
    token = create_access_token(subject="user_a", roles=["customer"])

    with TestClient(gateway_app) as client:
        response = client.get(
            "/api/v1/cart/user_b",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403


def test_cart_rejects_client_controlled_price_payload() -> None:
    with TestClient(cart_app) as client:
        response = client.post(
            "/cart/items",
            json={
                "user_id": "user_123",
                "product_id": "00000000-0000-0000-0000-000000000001",
                "quantity": 1,
                "unit_price": "0.01",
            },
        )

    assert response.status_code == 422


def test_gateway_rate_limit_blocks_excess_requests(monkeypatch) -> None:
    fake_rate_limit = FakeRateLimitClient()
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", True)
    monkeypatch.setattr(settings, "gateway_rate_limit_per_minute", 1)
    monkeypatch.setattr(settings, "jwt_secret_key", SecretStr("x" * 32))
    monkeypatch.setattr(proxy_client.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        rate_limit_store,
        "get_rate_limit_client",
        lambda: fake_rate_limit,
    )
    token = create_access_token(subject="user_123", roles=["customer"])

    with TestClient(gateway_app) as client:
        first = client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {token}"},
        )
        second = client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
