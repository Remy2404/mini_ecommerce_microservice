import asyncio
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.auth_service.app.application.services import AuthService
from apps.auth_service.app.main import app
from apps.auth_service.app.schemas.requests import RegisterUserRequest
from apps.auth_service.app.schemas.responses import RegisterUserResponse
from packages.config.settings import settings
from packages.security import wso2_login, wso2_scim
from packages.security.passwords import hash_password, verify_password
from packages.security.wso2_scim import WSO2SCIMError, register_wso2_user


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


class FakeSCIMAsyncClient:
    calls: list[dict] = []
    token_response: httpx.Response = httpx.Response(
        200,
        json={
            "access_token": "service-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )
    user_create_response: httpx.Response | None = None

    def __init__(self, *args, **kwargs) -> None:
        self.__class__.calls.append({"method": "INIT", **kwargs})

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, url: str, **kwargs) -> httpx.Response:
        self.__class__.calls.append({"method": "POST", "url": url, **kwargs})
        if url.endswith("/oauth2/token"):
            return self.__class__.token_response

        if self.__class__.user_create_response is not None:
            return self.__class__.user_create_response

        payload = kwargs.get("json", {})

        return httpx.Response(
            201,
            json={
                "id": "wso2-user-id",
                "userName": payload["userName"],
                "emails": payload["emails"],
                "groups": payload.get("groups", []),
            },
        )


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


def test_scim_register_creates_wso2_user_with_scim_payload(
    monkeypatch,
) -> None:
    FakeSCIMAsyncClient.calls = []
    FakeSCIMAsyncClient.token_response = httpx.Response(
        200,
        json={
            "access_token": "service-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )
    FakeSCIMAsyncClient.user_create_response = None
    monkeypatch.setattr(wso2_scim.httpx, "AsyncClient", FakeSCIMAsyncClient)
    monkeypatch.setattr(settings, "wso2_base_url", "https://wso2.local")
    monkeypatch.setattr(settings, "wso2_token_url", "https://wso2.local/oauth2/token")
    monkeypatch.setattr(settings, "wso2_client_id", "local-client-id")
    monkeypatch.setattr(settings, "wso2_client_secret", "local-client-secret")
    monkeypatch.setattr(settings, "wso2_scim_create_scope", "internal_user_mgt_create")
    monkeypatch.setattr(settings, "wso2_request_timeout_seconds", 7.5)
    monkeypatch.setattr(settings, "wso2_verify_ssl", False)

    registered = asyncio.run(
        register_wso2_user(
            username="john.doe",
            email="ramy@example.com",
            password="StrongPass@123",
            given_name="John",
            family_name="Doe",
        )
    )
    service_token = FakeSCIMAsyncClient.calls[1]
    user_create = FakeSCIMAsyncClient.calls[2]

    assert registered == {
        "id": "wso2-user-id",
        "username": "john.doe",
        "email": "ramy@example.com",
        "message": "User registered successfully",
    }
    assert service_token["method"] == "POST"
    assert service_token["url"] == "https://wso2.local/oauth2/token"
    assert service_token["data"] == {
        "grant_type": "client_credentials",
        "scope": "internal_user_mgt_create",
    }
    assert service_token["auth"] == ("local-client-id", "local-client-secret")

    user_payload = user_create["json"]
    assert user_payload["userName"] == "john.doe"
    assert user_payload["name"] == {"givenName": "John", "familyName": "Doe"}
    assert user_payload["emails"] == [{"value": "ramy@example.com", "primary": True}]
    assert user_payload["password"] == "StrongPass@123"
    assert user_create["headers"]["Content-Type"] == "application/scim+json"
    assert [call["method"] for call in FakeSCIMAsyncClient.calls] == [
        "INIT",
        "POST",
        "POST",
    ]


@pytest.mark.parametrize(
    ("upstream_status", "upstream_body", "expected_status", "expected_message"),
    [
        (
            400,
            {"scimType": "invalidValue", "status": "400"},
            400,
            "Invalid registration request",
        ),
        (
            401,
            {"error": "invalid_client", "status": "401"},
            503,
            "WSO2 registration configuration error",
        ),
        (
            403,
            {"error": "forbidden", "status": "403"},
            503,
            "WSO2 registration configuration error",
        ),
        (
            409,
            {"scimType": "uniqueness", "status": "409"},
            409,
            "User already exists",
        ),
    ],
)
def test_scim_register_maps_safe_wso2_error_statuses(
    monkeypatch,
    upstream_status: int,
    upstream_body: dict,
    expected_status: int,
    expected_message: str,
) -> None:
    FakeSCIMAsyncClient.calls = []
    FakeSCIMAsyncClient.token_response = httpx.Response(
        200,
        json={"access_token": "service-access-token"},
    )
    FakeSCIMAsyncClient.user_create_response = httpx.Response(
        upstream_status,
        json=upstream_body,
    )
    monkeypatch.setattr(wso2_scim.httpx, "AsyncClient", FakeSCIMAsyncClient)
    monkeypatch.setattr(settings, "wso2_base_url", "https://wso2.local")
    monkeypatch.setattr(settings, "wso2_scim_create_scope", "internal_user_mgt_create")

    with pytest.raises(WSO2SCIMError) as exc_info:
        asyncio.run(
            register_wso2_user(
                username="john.doe",
                email="ramy@example.com",
                password="strong-password",
                given_name="John",
                family_name="Doe",
            )
        )

    assert exc_info.value.status_code == expected_status
    assert exc_info.value.message == expected_message
    assert exc_info.value.target_url == "https://wso2.local/scim2/Users"
    assert exc_info.value.wso2_error_code in {
        upstream_body.get("scimType"),
        upstream_body.get("error"),
        upstream_body.get("status"),
    }


def test_current_user_rejects_application_token() -> None:
    with pytest.raises(WSO2SCIMError) as exc_info:
        asyncio.run(
            wso2_scim.current_wso2_user(
                {
                    "sub": "client-credentials-subject",
                    "aut": "APPLICATION",
                }
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.message == "User token required"


def test_current_user_uses_userinfo_when_token_email_is_missing(monkeypatch) -> None:
    async def fake_userinfo(access_token: str, *, request_id: str | None = None):
        assert access_token == "user-access-token"
        assert request_id == "request-123"
        return {
            "sub": "wso2-user-id",
            "email": "ramy@example.com",
        }

    monkeypatch.setattr(wso2_scim, "get_wso2_userinfo", fake_userinfo)

    user = asyncio.run(
        wso2_scim.current_wso2_user(
            {
                "sub": "wso2-user-id",
                "aut": "APPLICATION_USER",
            },
            access_token="user-access-token",
            request_id="request-123",
        )
    )

    assert user == {
        "user_id": "wso2-user-id",
        "username": "ramy@example.com",
        "email": "ramy@example.com",
        "roles": [],
    }


def test_password_hash_is_verifiable_and_not_plaintext() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_register_user_creates_wso2_user(monkeypatch) -> None:
    repository = FakeAuthRepository()
    service = AuthService(repository=repository)

    async def fake_register_wso2_user(
        *,
        username: str,
        email: str,
        password: str,
        given_name: str,
        family_name: str,
        request_id: str | None = None,
    ):
        assert username == "john.doe"
        assert email == "ramy@example.com"
        assert password == "StrongPass@123"
        assert given_name == "John"
        assert family_name == "Doe"
        assert request_id is None
        return {
            "id": "wso2-user-id",
            "username": username,
            "email": email,
            "message": "User registered successfully",
        }

    monkeypatch.setattr(
        "apps.auth_service.app.application.services.register_wso2_user",
        fake_register_wso2_user,
    )

    registered = asyncio.run(
        service.register_user(
            RegisterUserRequest(
                username="john.doe",
                email="ramy@example.com",
                password=SecretStr("StrongPass@123"),
                given_name="John",
                family_name="Doe",
            )
        )
    )

    assert registered.id == "wso2-user-id"
    assert registered.username == "john.doe"
    assert registered.email == "ramy@example.com"
    assert registered.message == "User registered successfully"
    assert repository.users_by_id == {}


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
    assert response.json()["refresh_token"] == "refresh-token"
    assert "success" not in response.json()
    assert FakeWSO2AsyncClient.init_kwargs == [{"timeout": 7.5, "verify": False}]
    assert FakeWSO2AsyncClient.post_requests[0]["url"] == "https://wso2.local/oauth2/token"


def test_wso2_admin_client_fields_are_not_required_anymore() -> None:
    model_fields = type(settings).model_fields

    assert "wso2_admin_client_id" not in model_fields
    assert "wso2_admin_client_secret" not in model_fields
    assert "wso2_admin_scope" not in model_fields
    assert "wso2_client_id" in model_fields
    assert "wso2_client_secret" in model_fields
    assert settings.wso2_scim_create_scope == "internal_user_mgt_create"


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
    user = RegisterUserResponse(
        id="wso2-user-id",
        username="john.doe",
        email="ramy@example.com",
        message="User registered successfully",
    )

    class FakeService:
        async def register_user(self, request, *, request_id=None):
            return user

    from apps.auth_service.app.api.routes import get_auth_service

    app.dependency_overrides[get_auth_service] = lambda: FakeService()
    try:
        with TestClient(app) as client:
            register_response = client.post(
                "/auth/register",
                json={
                    "username": "john.doe",
                    "email": "ramy@example.com",
                    "password": "StrongPass@123",
                    "given_name": "John",
                    "family_name": "Doe",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert register_response.status_code == 201
    assert register_response.json()["message"] == "User registered successfully"
    assert register_response.json()["data"]["id"] == "wso2-user-id"
    assert register_response.json()["data"]["username"] == "john.doe"
    assert register_response.json()["data"]["email"] == "ramy@example.com"


@pytest.mark.parametrize(
    ("exc", "expected_status", "expected_detail"),
    [
        (
            WSO2SCIMError(
                "Invalid registration request",
                status_code=400,
                error_type="scim_registration_bad_request",
            ),
            400,
            "Invalid registration request",
        ),
        (
            WSO2SCIMError(
                "WSO2 registration configuration error",
                status_code=503,
                error_type="scim_registration_configuration_error",
            ),
            503,
            "WSO2 registration configuration error",
        ),
        (
            WSO2SCIMError(
                "User already exists",
                status_code=409,
                error_type="scim_registration_conflict",
            ),
            409,
            "User already exists",
        ),
    ],
)
def test_auth_register_route_preserves_safe_scim_error_mapping(
    exc: WSO2SCIMError,
    expected_status: int,
    expected_detail: str,
) -> None:
    class FakeService:
        async def register_user(self, request, *, request_id=None):
            raise exc

    from apps.auth_service.app.api.routes import get_auth_service

    app.dependency_overrides[get_auth_service] = lambda: FakeService()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/auth/register",
                json={
                    "username": "john.doe",
                    "email": "ramy@example.com",
                    "password": "StrongPass@123",
                    "given_name": "John",
                    "family_name": "Doe",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}


def test_auth_me_requires_application_user_token() -> None:
    from apps.auth_service.app.api.dependencies import get_current_token_payload

    app.dependency_overrides[get_current_token_payload] = lambda: {
        "sub": "client-credentials-subject",
        "aut": "APPLICATION",
    }
    try:
        with TestClient(app) as client:
            response = client.get(
                "/auth/me",
                headers={"Authorization": "Bearer client-credentials-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "User token required"}
