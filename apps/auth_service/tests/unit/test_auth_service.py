import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.auth_service.app.api import routes as auth_routes
from apps.auth_service.app.application.services import AuthService
from apps.auth_service.app.main import app
from apps.auth_service.app.schemas.requests import RegisterUserRequest
from apps.auth_service.app.schemas.responses import RegisterUserResponse
from packages.config.settings import settings
from packages.security import wso2_login, wso2_scim
from packages.security.passwords import hash_password, verify_password
from packages.security.wso2_scim import WSO2SCIMError, register_wso2_user


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
    get_response: httpx.Response = httpx.Response(200, json={})
    get_error: httpx.HTTPError | None = None

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

    async def get(self, url: str, **kwargs) -> httpx.Response:
        self.__class__.calls.append({"method": "GET", "url": url, **kwargs})
        if self.__class__.get_error is not None:
            raise self.__class__.get_error
        return self.__class__.get_response


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


def _reset_fake_scim_client() -> None:
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
    FakeSCIMAsyncClient.get_response = httpx.Response(200, json={})
    FakeSCIMAsyncClient.get_error = None


def _sample_scim_user(**overrides) -> dict:
    user = {
        "id": "wso2-user-id",
        "userName": "john.doe",
        "name": {"givenName": "John", "familyName": "Doe"},
        "emails": [{"value": "john@example.com", "primary": True}],
        "active": True,
        "groups": [{"display": "customer"}],
    }
    user.update(overrides)
    return user


def _sample_users_response() -> dict:
    return {
        "totalResults": 2,
        "startIndex": 1,
        "itemsPerPage": 2,
        "Resources": [
            _sample_scim_user(id="user-1", userName="john.doe"),
            _sample_scim_user(
                id="user-2",
                userName="jane.doe",
                name={"givenName": "Jane", "familyName": "Doe"},
                emails=[{"value": "jane@example.com"}],
                groups=[{"displayName": "admin"}],
            ),
        ],
    }


def _sample_user_profile(**overrides) -> dict:
    user = {
        "id": "wso2-user-id",
        "username": "john.doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "active": True,
        "roles": ["customer"],
    }
    user.update(overrides)
    return user


def _configure_scim(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_fake_scim_client()
    monkeypatch.setattr(wso2_scim.httpx, "AsyncClient", FakeSCIMAsyncClient)
    monkeypatch.setattr(settings, "wso2_base_url", "https://wso2.local")
    monkeypatch.setattr(settings, "wso2_token_url", "https://wso2.local/oauth2/token")
    monkeypatch.setattr(settings, "wso2_client_id", "local-client-id")
    monkeypatch.setattr(settings, "wso2_client_secret", "local-client-secret")
    monkeypatch.setattr(settings, "wso2_scim_create_scope", "internal_user_mgt_create")
    monkeypatch.setattr(settings, "wso2_scim_view_scope", "internal_user_mgt_view")
    monkeypatch.setattr(settings, "wso2_scim_list_scope", "internal_user_mgt_list")
    monkeypatch.setattr(settings, "wso2_request_timeout_seconds", 7.5)
    monkeypatch.setattr(settings, "wso2_verify_ssl", False)


def test_scim_register_creates_wso2_user_with_scim_payload(monkeypatch) -> None:
    _configure_scim(monkeypatch)

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
            502,
            "WSO2 service credential error",
        ),
        (
            403,
            {"error": "forbidden", "status": "403"},
            403,
            "Insufficient WSO2 scope for this operation",
        ),
        (409, {"scimType": "uniqueness", "status": "409"}, 409, "User already exists"),
    ],
)
def test_scim_register_maps_safe_wso2_error_statuses(
    monkeypatch,
    upstream_status: int,
    upstream_body: dict,
    expected_status: int,
    expected_message: str,
) -> None:
    _configure_scim(monkeypatch)
    FakeSCIMAsyncClient.user_create_response = httpx.Response(
        upstream_status,
        json=upstream_body,
    )

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


def test_filter_wso2_users_success(monkeypatch) -> None:
    _configure_scim(monkeypatch)
    FakeSCIMAsyncClient.get_response = httpx.Response(
        200, json=_sample_users_response()
    )

    result = asyncio.run(
        wso2_scim.filter_wso2_users(
            filter_query='userName co "doe"',
            attributes="id,userName",
            excluded_attributes="groups",
            start_index=1,
            count=2,
            domain="PRIMARY",
            request_id="request-123",
        )
    )

    token_call = FakeSCIMAsyncClient.calls[1]
    list_call = FakeSCIMAsyncClient.calls[2]
    assert token_call["data"]["scope"] == "internal_user_mgt_list"
    assert list_call["method"] == "GET"
    assert list_call["url"] == "https://wso2.local/scim2/Users"
    assert list_call["params"] == {
        "startIndex": 1,
        "count": 2,
        "filter": 'userName co "doe"',
        "attributes": "id,userName",
        "excludedAttributes": "groups",
        "domain": "PRIMARY",
    }
    assert result == {
        "total_results": 2,
        "start_index": 1,
        "items_per_page": 2,
        "users": [
            {
                "id": "user-1",
                "username": "john.doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "active": True,
                "roles": ["customer"],
            },
            {
                "id": "user-2",
                "username": "jane.doe",
                "email": "jane@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "active": True,
                "roles": ["admin"],
            },
        ],
    }


@pytest.mark.parametrize(
    ("upstream_status", "expected_status", "expected_message"),
    [
        (401, 502, "WSO2 service credential error"),
        (403, 403, "Insufficient WSO2 scope for this operation"),
    ],
)
def test_filter_wso2_users_maps_wso2_auth_errors(
    monkeypatch,
    upstream_status: int,
    expected_status: int,
    expected_message: str,
) -> None:
    _configure_scim(monkeypatch)
    FakeSCIMAsyncClient.get_response = httpx.Response(
        upstream_status,
        json={"error": "upstream-error"},
    )

    with pytest.raises(WSO2SCIMError) as exc_info:
        asyncio.run(wso2_scim.filter_wso2_users())

    assert exc_info.value.status_code == expected_status
    assert exc_info.value.message == expected_message


def test_search_users_escapes_filter_injection(monkeypatch) -> None:
    captured: dict = {}

    async def fake_filter_wso2_users(**kwargs):
        captured.update(kwargs)
        return {"total_results": 0, "start_index": 1, "items_per_page": 0, "users": []}

    monkeypatch.setattr(wso2_scim, "filter_wso2_users", fake_filter_wso2_users)

    result = asyncio.run(
        wso2_scim.search_wso2_users(
            query='a"\\b',
            start_index=3,
            count=4,
            request_id="request-123",
        )
    )

    assert result["users"] == []
    assert captured == {
        "filter_query": 'userName co "a\\"\\\\b" or emails co "a\\"\\\\b"',
        "start_index": 3,
        "count": 4,
        "request_id": "request-123",
    }


def test_search_users_success(monkeypatch) -> None:
    _configure_scim(monkeypatch)
    FakeSCIMAsyncClient.get_response = httpx.Response(
        200, json=_sample_users_response()
    )

    result = asyncio.run(
        wso2_scim.search_wso2_users(query="doe", start_index=1, count=2)
    )

    list_call = FakeSCIMAsyncClient.calls[2]
    assert list_call["params"]["filter"] == 'userName co "doe" or emails co "doe"'
    assert result["total_results"] == 2
    assert [user["username"] for user in result["users"]] == ["john.doe", "jane.doe"]


def test_get_user_by_id_success(monkeypatch) -> None:
    _configure_scim(monkeypatch)
    FakeSCIMAsyncClient.get_response = httpx.Response(
        200,
        json=_sample_scim_user(),
    )

    result = asyncio.run(wso2_scim.get_wso2_user_by_id("wso2-user-id"))

    token_call = FakeSCIMAsyncClient.calls[1]
    get_call = FakeSCIMAsyncClient.calls[2]
    assert token_call["data"]["scope"] == "internal_user_mgt_view"
    assert get_call["url"] == "https://wso2.local/scim2/Users/wso2-user-id"
    assert result == {
        "user": {
            "id": "wso2-user-id",
            "username": "john.doe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "active": True,
            "roles": ["customer"],
        }
    }


def test_get_user_by_id_404(monkeypatch) -> None:
    _configure_scim(monkeypatch)
    FakeSCIMAsyncClient.get_response = httpx.Response(
        404,
        json={"status": "404"},
    )

    with pytest.raises(WSO2SCIMError) as exc_info:
        asyncio.run(wso2_scim.get_wso2_user_by_id("missing-user"))

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "User not found"


def test_get_user_by_id_wso2_unreachable(monkeypatch) -> None:
    _configure_scim(monkeypatch)
    FakeSCIMAsyncClient.get_error = httpx.ConnectError("connection failed")

    with pytest.raises(WSO2SCIMError) as exc_info:
        asyncio.run(wso2_scim.get_wso2_user_by_id("wso2-user-id"))

    assert exc_info.value.status_code == 502
    assert exc_info.value.message == "Authentication service unavailable"


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


def test_current_user_fallback_keeps_legacy_shape(monkeypatch) -> None:
    async def fake_get_wso2_user_by_id(user_id: str, *, request_id: str | None = None):
        assert user_id == "wso2-user-id"
        assert request_id == "request-123"
        return {
            "user": {
                "id": "wso2-user-id",
                "username": "john.doe",
                "email": "john@example.com",
                "roles": ["customer"],
            }
        }

    monkeypatch.setattr(wso2_scim, "get_wso2_user_by_id", fake_get_wso2_user_by_id)

    user = asyncio.run(
        wso2_scim.current_wso2_user(
            {
                "sub": "wso2-user-id",
                "aut": "APPLICATION_USER",
            },
            request_id="request-123",
        )
    )

    assert user == {
        "user_id": "wso2-user-id",
        "username": "john.doe",
        "email": "john@example.com",
        "roles": ["customer"],
    }


def test_password_hash_is_verifiable_and_not_plaintext() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_register_user_creates_wso2_user(monkeypatch) -> None:
    service = AuthService()

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
                first_name="John",
                last_name="Doe",
            )
        )
    )

    assert registered.id == "wso2-user-id"
    assert registered.username == "john.doe"
    assert registered.email == "ramy@example.com"
    assert registered.message == "User registered successfully"


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
    assert (
        FakeWSO2AsyncClient.post_requests[0]["url"] == "https://wso2.local/oauth2/token"
    )


def test_wso2_admin_client_fields_are_not_required_anymore() -> None:
    model_fields = type(settings).model_fields

    assert "wso2_admin_client_id" not in model_fields
    assert "wso2_admin_client_secret" not in model_fields
    assert "wso2_admin_scope" not in model_fields
    assert "wso2_client_id" in model_fields
    assert "wso2_client_secret" in model_fields
    assert settings.wso2_scim_create_scope == "internal_user_mgt_create"
    assert settings.wso2_scim_list_scope == "internal_user_mgt_list"


def test_hidden_internal_wso2_login_returns_safe_error_for_bad_credentials(
    monkeypatch,
) -> None:
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


def test_auth_register_route_returns_stable_envelope(monkeypatch) -> None:
    user = RegisterUserResponse(
        id="wso2-user-id",
        username="john.doe",
        email="ramy@example.com",
        message="User registered successfully",
    )

    class FakeService:
        async def register_user(self, request, *, request_id=None):
            assert request.first_name == "John"
            assert request.last_name == "Doe"
            return user

    app.dependency_overrides[auth_routes.get_auth_service] = lambda: FakeService()
    try:
        with TestClient(app) as client:
            register_response = client.post(
                "/auth/register",
                json={
                    "username": "john.doe",
                    "email": "ramy@example.com",
                    "password": "StrongPass@123",
                    "first_name": "John",
                    "last_name": "Doe",
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
                "WSO2 service credential error",
                status_code=502,
                error_type="scim_registration_credential_error",
            ),
            502,
            "WSO2 service credential error",
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

    app.dependency_overrides[auth_routes.get_auth_service] = lambda: FakeService()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/auth/register",
                json={
                    "username": "john.doe",
                    "email": "ramy@example.com",
                    "password": "StrongPass@123",
                    "first_name": "John",
                    "last_name": "Doe",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}


def test_list_users_route_returns_envelope(monkeypatch) -> None:
    captured: dict = {}

    async def fake_filter_wso2_users(**kwargs):
        captured.update(kwargs)
        return {
            "total_results": 1,
            "start_index": 2,
            "items_per_page": 1,
            "users": [_sample_user_profile()],
        }

    monkeypatch.setattr(auth_routes, "filter_wso2_users", fake_filter_wso2_users)

    with TestClient(app) as client:
        response = client.get(
            "/auth/users",
            params={
                "filter": 'userName co "john"',
                "attributes": "id,userName",
                "excludedAttributes": "groups",
                "startIndex": 2,
                "count": 1,
                "domain": "PRIMARY",
            },
            headers={"x-request-id": "request-123"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Users retrieved successfully"
    assert response.json()["data"]["total_results"] == 1
    assert captured == {
        "filter_query": 'userName co "john"',
        "attributes": "id,userName",
        "excluded_attributes": "groups",
        "start_index": 2,
        "count": 1,
        "domain": "PRIMARY",
        "request_id": "request-123",
    }


def test_search_users_route_returns_envelope(monkeypatch) -> None:
    captured: dict = {}

    async def fake_search_wso2_users(**kwargs):
        captured.update(kwargs)
        return {
            "total_results": 0,
            "start_index": 1,
            "items_per_page": 0,
            "users": [],
        }

    monkeypatch.setattr(auth_routes, "search_wso2_users", fake_search_wso2_users)

    with TestClient(app) as client:
        response = client.get(
            "/auth/users/search",
            params={"q": "john", "startIndex": 1, "count": 25},
            headers={"x-request-id": "request-123"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Search results retrieved successfully"
    assert response.json()["data"]["users"] == []
    assert captured == {
        "query": "john",
        "start_index": 1,
        "count": 25,
        "request_id": "request-123",
    }


def test_get_user_route_returns_envelope(monkeypatch) -> None:
    captured: dict = {}

    async def fake_get_wso2_user_by_id(user_id: str, *, request_id: str | None = None):
        captured["user_id"] = user_id
        captured["request_id"] = request_id
        return {
            "user": {
                "id": user_id,
                "username": "john.doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "active": True,
                "roles": ["customer"],
            }
        }

    monkeypatch.setattr(auth_routes, "get_wso2_user_by_id", fake_get_wso2_user_by_id)

    with TestClient(app) as client:
        response = client.get(
            "/auth/users/wso2-user-id",
            headers={"x-request-id": "request-123"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "User retrieved successfully"
    assert response.json()["data"]["user"]["id"] == "wso2-user-id"
    assert captured == {"user_id": "wso2-user-id", "request_id": "request-123"}
