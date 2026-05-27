from uuid import uuid4

from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.auth_service.app.application.services import AuthService
from apps.auth_service.app.main import app
from apps.auth_service.app.schemas.requests import LoginRequest, RegisterUserRequest
from apps.auth_service.app.schemas.responses import AuthTokenResponse, UserProfileResponse
from packages.config.settings import settings
from packages.security.jwt import decode_access_token
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


def test_password_hash_is_verifiable_and_not_plaintext() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_register_and_login_issue_jwt(monkeypatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret_key", SecretStr("x" * 32))
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
    token = asyncio.run(
        service.login_user(
            LoginRequest(email="ramy@example.com", password=SecretStr("strong-password"))
        )
    )

    payload = decode_access_token(token.access_token)
    assert registered.email == "ramy@example.com"
    assert payload["sub"] == str(registered.user_id)
    assert payload["roles"] == ["customer"]


def test_auth_routes_return_stable_envelope(monkeypatch) -> None:
    user_id = uuid4()
    user = UserProfileResponse(
        user_id=user_id,
        email="ramy@example.com",
        full_name="Ramy",
        is_active=True,
        roles=["customer"],
    )
    token = AuthTokenResponse(access_token="token", user=user)

    class FakeService:
        async def register_user(self, request):
            return user

        async def login_user(self, request):
            return token

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
            login_response = client.post(
                "/auth/login",
                json={"email": "ramy@example.com", "password": "strong-password"},
            )
    finally:
        app.dependency_overrides.clear()

    assert register_response.status_code == 201
    assert register_response.json()["data"]["email"] == "ramy@example.com"
    assert login_response.status_code == 200
    assert login_response.json()["data"]["access_token"] == "token"
