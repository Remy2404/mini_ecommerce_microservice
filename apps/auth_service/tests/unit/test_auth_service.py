from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.auth_service.app.application.services import AuthService
from apps.auth_service.app.main import app
from apps.auth_service.app.schemas.requests import RegisterUserRequest
from apps.auth_service.app.schemas.responses import UserProfileResponse
from packages.config.settings import settings
from packages.security import wso2_login
from packages.security.passwords import hash_password, verify_password


class FakeAuthRepository:
    def __init__(self) -> None:
        self.users_by_email = {}
        self.users_by_id = {}
        self.roles_by_user = {}

    async def get_user_by_email(self, email: str):
        return self.users_by_email.get(email)

    async def get_user_by_id(self, user_id):
        return self.users_by_id.get(user_id)

    async def create_user(self, *, user_id, email, password_hash, full_name) -> None:
        record = type(
            "UserRecord",
            (),
            {
                "user_id": user_id,
                "email": email,
                "password_hash": password_hash,
                "full_name": full_name,
                "is_active": True,
            },
        )()
        self.users_by_email[email] = record
        self.users_by_id[user_id] = record

    async def ensure_role(self, name, description):
        return type("Role", (), {"role_id": uuid4(), "name": name, "description": description})()

    async def assign_role(self, user_id, role_name) -> None:
        self.roles_by_user.setdefault(user_id, []).append(
            type("Role", (), {"role_id": uuid4(), "name": role_name, "description": None})()
        )

    async def list_roles(self, user_id):
        return self.roles_by_user.get(user_id, [])


class FakeWSO2AsyncClient:
    init_kwargs: list[dict] = []
    post_requests: list[dict] = []
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
        self.__class__.post_requests.append({"url": url, **kwargs})
        return self.__class__.response


def _reset_fake_wso2_client() -> None:
    FakeWSO2AsyncClient.init_kwargs = []
    FakeWSO2AsyncClient.post_requests = []
    FakeWSO2AsyncClient.response = httpx.Response(
        200,
        json={
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )


def test_password_hash_is_verifiable_and_not_plaintext() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_register_user_still_creates_profile() -> None:
    repository = FakeAuthRepository()
    service = AuthService(repository=repository)

    import asyncio

    registered = asyncio.run(
        service.register_user(
            RegisterUserRequest(
                email="ramy@example.com",
                password=SecretStr("strong-password"),
                full_name="Ramy",
            )
        )
    )

    assert registered.email == "ramy@example.com"


def test_hidden_internal_wso2_login_returns_token_response(monkeypatch) -> None:
    _reset_fake_wso2_client()
    monkeypatch.setattr(wso2_login.httpx, "AsyncClient", FakeWSO2AsyncClient)
    monkeypatch.setattr(settings, "wso2_token_url", "https://wso2.local/oauth2/token")
    monkeypatch.setattr(settings, "wso2_client_id", "local-client-id")
    monkeypatch.setattr(settings, "wso2_client_secret", "local-client-secret")
    monkeypatch.setattr(settings, "wso2_request_timeout_seconds", 7.5)
    monkeypatch.setattr(settings, "wso2_verify_ssl", False)

    with TestClient(app) as client:
        response = client.post(
            "/internal/wso2/login",
            json={
                "username": "admin",
                "password": "admin",
                "scope": "openid profile",
            },
        )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access-token"
    assert FakeWSO2AsyncClient.init_kwargs == [{"timeout": 7.5, "verify": False}]
    assert FakeWSO2AsyncClient.post_requests[0]["url"] == "https://wso2.local/oauth2/token"


def test_hidden_internal_wso2_login_returns_safe_error_for_bad_credentials(monkeypatch) -> None:
    _reset_fake_wso2_client()
    FakeWSO2AsyncClient.response = httpx.Response(401, json={"error": "invalid_grant"})
    monkeypatch.setattr(wso2_login.httpx, "AsyncClient", FakeWSO2AsyncClient)

    with TestClient(app) as client:
        response = client.post(
            "/internal/wso2/login",
            json={
                "username": "admin",
                "password": "wrong",
                "scope": "openid profile",
            },
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


def test_auth_routes_return_stable_envelope(monkeypatch) -> None:
    user_id = uuid4()
    user = UserProfileResponse(
        user_id=user_id,
        email="ramy@example.com",
        full_name="Ramy",
        is_active=True,
        roles=["customer"],
    )

    class FakeService:
        async def register_user(self, request):
            return user

    from apps.auth_service.app.api.routes import get_auth_service

    app.dependency_overrides[get_auth_service] = lambda: FakeService()
    try:
        with TestClient(app) as client:
            register_response = client.post(
                "/auth/register",
                json={
                    "email": "ramy@example.com",
                    "password": "strong-password",
                    "full_name": "Ramy",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert register_response.status_code == 201
    assert register_response.json()["data"]["email"] == "ramy@example.com"
