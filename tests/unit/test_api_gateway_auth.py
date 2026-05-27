import anyio
import httpx
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from packages.config.settings import settings
from app.services.api_gateway.app.dependencies import auth


class FakeAsyncClient:
    init_kwargs: list[dict] = []
    requested_urls: list[str] = []
    posted_requests: list[dict] = []
    post_response: httpx.Response = httpx.Response(200, json={"active": True})

    def __init__(self, *args, **kwargs) -> None:
        self.__class__.init_kwargs.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def get(self, url: str) -> httpx.Response:
        self.__class__.requested_urls.append(url)
        return httpx.Response(200, json={"keys": []}, request=httpx.Request("GET", url))

    async def post(self, url: str, **kwargs) -> httpx.Response:
        self.__class__.posted_requests.append({"url": url, **kwargs})
        return self.__class__.post_response


def _reset_jwks_cache() -> None:
    auth._jwks_cache = {}
    FakeAsyncClient.init_kwargs = []
    FakeAsyncClient.requested_urls = []
    FakeAsyncClient.posted_requests = []
    FakeAsyncClient.post_response = httpx.Response(200, json={"active": True})


def test_auth_disabled_allows_local_request(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gateway_auth_enabled", False)

    payload = anyio.run(auth.validate_token, None)

    assert payload == {"sub": "local-demo"}


def test_auth_enabled_without_token_returns_401(monkeypatch) -> None:
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)

    with pytest.raises(HTTPException) as exc_info:
        anyio.run(auth.validate_token, None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing bearer token"


def test_jwks_client_uses_shared_wso2_settings(monkeypatch) -> None:
    _reset_jwks_cache()
    monkeypatch.setattr(auth.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "wso2_jwks_url", "https://wso2.local/oauth2/jwks")
    monkeypatch.setattr(settings, "wso2_request_timeout_seconds", 7.5)
    monkeypatch.setattr(settings, "wso2_verify_ssl", False)

    jwks = anyio.run(auth.get_jwks)

    assert jwks == {"keys": []}
    assert FakeAsyncClient.requested_urls == ["https://wso2.local/oauth2/jwks"]
    assert FakeAsyncClient.init_kwargs == [
        {
            "timeout": 7.5,
            "verify": False,
        }
    ]


def test_auth_enabled_invalid_token_returns_401(monkeypatch) -> None:
    async def fake_get_jwks() -> dict:
        return {"keys": []}

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="bad.jwt.token",
    )
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(auth, "get_jwks", fake_get_jwks)

    with pytest.raises(HTTPException) as exc_info:
        anyio.run(auth.validate_token, credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


def test_auth_enabled_opaque_access_token_uses_wso2_introspection(monkeypatch) -> None:
    _reset_jwks_cache()
    FakeAsyncClient.post_response = httpx.Response(
        200,
        json={
            "active": True,
            "sub": "user-123",
            "scope": "openid profile email",
            "client_id": "local-client-id",
        },
    )
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="opaque-access-token",
    )
    monkeypatch.setattr(auth.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(
        settings, "wso2_introspection_url", "https://wso2.local/oauth2/introspect"
    )
    monkeypatch.setattr(settings, "wso2_client_id", "local-client-id")
    monkeypatch.setattr(settings, "wso2_client_secret", "local-client-secret")
    monkeypatch.setattr(settings, "wso2_request_timeout_seconds", 7.5)
    monkeypatch.setattr(settings, "wso2_verify_ssl", False)

    payload = anyio.run(auth.validate_token, credentials)

    assert payload["sub"] == "user-123"
    assert FakeAsyncClient.requested_urls == []
    assert FakeAsyncClient.init_kwargs == [{"timeout": 7.5, "verify": False}]
    assert FakeAsyncClient.posted_requests == [
        {
            "url": "https://wso2.local/oauth2/introspect",
            "data": {
                "token": "opaque-access-token",
                "token_type_hint": "access_token",
            },
            "auth": ("local-client-id", "local-client-secret"),
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        }
    ]


def test_auth_enabled_inactive_opaque_access_token_returns_401(monkeypatch) -> None:
    _reset_jwks_cache()
    FakeAsyncClient.post_response = httpx.Response(200, json={"active": False})
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="opaque-access-token",
    )
    monkeypatch.setattr(auth.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)

    with pytest.raises(HTTPException) as exc_info:
        anyio.run(auth.validate_token, credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"
