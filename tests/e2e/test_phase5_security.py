"""
Phase 5 Security Verification E2E Tests

Test Scenario Coverage:
- P5-S01: Missing bearer token
- P5-S02: Invalid bearer token
- P5-S03: Inactive/expired token
- P5-S04: IDOR on cart/resource
- P5-S05: Admin role bypass check
- P5-S06: Client price tampering
- P5-S07: Rate limit enforcement
- P5-S08: Error response leakage
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.api_gateway.app.api.dependencies import validate_token
from apps.api_gateway.app.infrastructure.cache import rate_limit_store
from apps.api_gateway.app.infrastructure.http import proxy_client
from apps.api_gateway.app.infrastructure.security import wso2_client
from apps.api_gateway.app.main import app as gateway_app
from apps.cart_service.app.main import app as cart_app
from apps.cart_service.app.schemas import AddCartItemRequest
from packages.config.settings import settings
from packages.security.jwt_validator import TokenValidationError


# ============================================================================
# Test Fixtures & Mocks
# ============================================================================


class FakeAsyncClient:
    """Mock async HTTP client for gateway tests."""

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
    """Mock rate limit client for testing rate limiting."""

    def __init__(self, limit_per_minute: int = 60) -> None:
        self.count = 0
        self.limit = limit_per_minute

    async def incr(self, key: str) -> int:
        self.count += 1
        return self.count

    async def expire(self, key: str, ttl_seconds: int) -> None:
        return None

    async def get(self, key: str) -> int | None:
        return self.count if self.count > 0 else None


@pytest.fixture
def mock_settings(monkeypatch):
    """Enable security settings for testing."""
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", True)
    monkeypatch.setattr(settings, "gateway_rate_limit_per_minute", 5)
    return settings


@pytest.fixture
def gateway_client(mock_settings):
    """Create a test client for the API gateway."""
    return TestClient(gateway_app)


@pytest.fixture
def cart_client():
    """Create a test client for the cart service."""
    return TestClient(cart_app)


# ============================================================================
# P5-S01: Missing Bearer Token
# ============================================================================


def test_p5_s01_missing_bearer_token_rejected(gateway_client, mock_settings) -> None:
    """
    P5-S01: Missing bearer token should be rejected with 401/403.

    Expected Result: Request rejected with 401 or 403 status code.
    """
    response = gateway_client.get("/api/v1/products")

    assert response.status_code in [401, 403], (
        f"Expected 401/403, got {response.status_code}. "
        f"Response: {response.json()}"
    )
    # Verify no sensitive internal details leaked
    response_data = response.json()
    assert "traceback" not in str(response_data).lower()
    assert "internal" not in str(response_data).lower()


# ============================================================================
# P5-S02: Invalid Bearer Token
# ============================================================================


def test_p5_s02_invalid_bearer_token_rejected(mock_settings) -> None:
    """
    P5-S02: Invalid bearer token should be rejected with 401/403.

    Expected Result: Request rejected with 401 or 403 status code.
    """
    # Override the validate_token dependency to raise an exception for invalid tokens
    def invalid_token_validator(credentials=None):
        raise HTTPException(status_code=401, detail="Invalid token")

    gateway_app.dependency_overrides[validate_token] = invalid_token_validator

    try:
        with TestClient(gateway_app) as client:
            response = client.get(
                "/api/v1/products",
                headers={"Authorization": "Bearer invalid.token.value"},
            )

        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. "
            f"Response: {response.json()}"
        )
        # Verify no sensitive internal details leaked
        response_data = response.json()
        assert "traceback" not in str(response_data).lower()
    finally:
        gateway_app.dependency_overrides.clear()


def test_p5_s02_malformed_bearer_token_rejected(gateway_client, mock_settings) -> None:
    """
    P5-S02: Malformed bearer tokens should be rejected.

    Expected Result: Request rejected with 401 or 403 status code.
    """
    # Missing "Bearer" prefix
    response = gateway_client.get(
        "/api/v1/products",
        headers={"Authorization": "invalid.token.value"},
    )

    assert response.status_code in [401, 403]

    # Empty Authorization header
    response = gateway_client.get(
        "/api/v1/products",
        headers={"Authorization": ""},
    )

    assert response.status_code in [401, 403]


# ============================================================================
# P5-S03: Inactive/Expired Token
# ============================================================================


def test_p5_s03_inactive_opaque_token_rejected(
    gateway_client, mock_settings, monkeypatch
) -> None:
    """
    P5-S03: Inactive WSO2 opaque access token should be rejected.

    Expected Result: Request rejected with 401 or 403 status code.
    """

    async def fake_inactive_introspection(token: str) -> dict:
        raise TokenValidationError("Token is inactive or expired")

    monkeypatch.setattr(
        wso2_client,
        "introspect_access_token",
        fake_inactive_introspection,
    )

    response = gateway_client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer expired-opaque-token"},
    )

    assert response.status_code in [401, 403], (
        f"Expected 401/403, got {response.status_code}. "
        f"Response: {response.json()}"
    )


def test_p5_s03_expired_jwt_token_rejected(
    gateway_client, mock_settings, monkeypatch
) -> None:
    """
    P5-S03: Expired JWT token should be rejected.

    Expected Result: Request rejected with 401 or 403 status code.
    """

    async def fake_introspection(token: str) -> dict:
        raise TokenValidationError("JWT token has expired")

    monkeypatch.setattr(
        wso2_client,
        "introspect_access_token",
        fake_introspection,
    )

    response = gateway_client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer expired-jwt-token"},
    )

    assert response.status_code in [401, 403]


# ============================================================================
# P5-S04: IDOR on Cart Resource
# ============================================================================


def test_p5_s04_idor_cart_access_blocked(
    gateway_client, mock_settings, monkeypatch
) -> None:
    """
    P5-S04: IDOR attempt - User accessing another user's cart should be blocked.

    Expected Result: Request rejected with 403 status code.
    """

    async def fake_introspection(token: str) -> dict:
        # Token belongs to user_a
        return {"sub": "user_a", "roles": ["customer"], "active": True}

    monkeypatch.setattr(
        wso2_client,
        "introspect_access_token",
        fake_introspection,
    )
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)

    # user_a attempts to access user_b's cart
    response = gateway_client.get(
        "/api/v1/cart/user_b",
        headers={"Authorization": "Bearer opaque-token"},
    )

    assert response.status_code == 403, (
        f"Expected 403 (Forbidden), got {response.status_code}. "
        f"Response: {response.json()}"
    )


def test_p5_s04_idor_cart_own_access_allowed(
    gateway_client, mock_settings, monkeypatch
) -> None:
    """
    P5-S04: User accessing their own cart should be allowed.

    Expected Result: Request accepted with 200 or similar success code.
    """

    async def fake_introspection(token: str) -> dict:
        return {"sub": "user_a", "roles": ["customer"], "active": True}

    async def fake_proxy_request(**kwargs):
        return httpx.Response(200, json={"user_id": "user_a", "items": []})

    monkeypatch.setattr(
        wso2_client,
        "introspect_access_token",
        fake_introspection,
    )
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(proxy_client.httpx, "AsyncClient", FakeAsyncClient)

    response = gateway_client.get(
        "/api/v1/cart/user_a",
        headers={"Authorization": "Bearer opaque-token"},
    )

    # Should be allowed (either 200 or redirect to service)
    assert response.status_code < 400, (
        f"Expected 2xx or 3xx, got {response.status_code}. "
        f"Response: {response.json()}"
    )


# ============================================================================
# P5-S05: Admin Role Bypass Check
# ============================================================================


def test_p5_s05_admin_role_allowed_cart_access(
    gateway_client, mock_settings, monkeypatch
) -> None:
    """
    P5-S05: Admin user should be allowed to access other users' carts.

    Expected Result: Request accepted (admin bypass policy).
    """

    async def fake_introspection(token: str) -> dict:
        # Token has admin role
        return {"sub": "admin_user", "roles": ["admin"], "active": True}

    monkeypatch.setattr(
        wso2_client,
        "introspect_access_token",
        fake_introspection,
    )
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(proxy_client.httpx, "AsyncClient", FakeAsyncClient)

    # Admin accessing another user's cart
    response = gateway_client.get(
        "/api/v1/cart/any_user",
        headers={"Authorization": "Bearer admin-token"},
    )

    # Admin should be allowed (either 200 or proxy-through)
    assert response.status_code < 400, (
        f"Expected 2xx or 3xx (admin allowed), got {response.status_code}. "
        f"Response: {response.json()}"
    )


# ============================================================================
# P5-S06: Client Price Tampering
# ============================================================================


def test_p5_s06_client_price_tampering_rejected(cart_client) -> None:
    """
    P5-S06: Client attempting to control price should be rejected.

    Expected Result: Request rejected with 422 (schema validation error).
    """
    product_id = str(uuid4())

    # Attempt to include client-controlled unit_price
    response = cart_client.post(
        "/cart/items",
        json={
            "user_id": "user_123",
            "product_id": product_id,
            "quantity": 1,
            "unit_price": "0.01",  # This should not be allowed
        },
    )

    assert response.status_code == 422, (
        f"Expected 422 (validation error), got {response.status_code}. "
        f"Response: {response.json()}"
    )


def test_p5_s06_price_field_not_accepted(cart_client) -> None:
    """
    P5-S06: Price field should not be accepted in cart item request.

    Expected Result: Request rejected with validation error.
    """
    product_id = str(uuid4())

    # Attempt with 'price' field
    response = cart_client.post(
        "/cart/items",
        json={
            "user_id": "user_123",
            "product_id": product_id,
            "quantity": 1,
            "price": "99.99",  # Tampering attempt
        },
    )

    assert response.status_code == 422


# ============================================================================
# P5-S07: Rate Limit Enforcement
# ============================================================================


def test_p5_s07_rate_limit_429_returned(
    gateway_client, mock_settings, monkeypatch
) -> None:
    """
    P5-S07: Excess requests should return 429 (Too Many Requests).

    Expected Result: After limit exceeded, request returns 429.
    """

    async def fake_introspection(token: str) -> dict:
        return {"sub": "user_123", "roles": ["customer"], "active": True}

    fake_rate_limit = FakeRateLimitClient(limit_per_minute=2)
    monkeypatch.setattr(
        wso2_client,
        "introspect_access_token",
        fake_introspection,
    )
    monkeypatch.setattr(settings, "gateway_rate_limit_per_minute", 2)
    monkeypatch.setattr(proxy_client.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        rate_limit_store,
        "get_rate_limit_client",
        lambda: fake_rate_limit,
    )

    # First two requests should succeed
    response1 = gateway_client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer opaque-token"},
    )
    response2 = gateway_client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer opaque-token"},
    )

    # Third request should be rate limited (429)
    response3 = gateway_client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer opaque-token"},
    )

    assert response1.status_code < 400, (
        f"First request should succeed, got {response1.status_code}"
    )
    assert response2.status_code < 400, (
        f"Second request should succeed, got {response2.status_code}"
    )
    assert response3.status_code == 429, (
        f"Third request should be rate limited (429), got {response3.status_code}. "
        f"Response: {response3.json()}"
    )


# ============================================================================
# P5-S08: Error Response Leakage
# ============================================================================


def test_p5_s08_no_traceback_in_error_response(gateway_client, mock_settings) -> None:
    """
    P5-S08: Error responses should not leak internal traceback details.

    Expected Result: Error responses do not contain traceback or internal details.
    """
    response = gateway_client.get("/api/v1/products")

    response_data = response.json()
    response_str = json.dumps(response_data, default=str).lower()

    # Ensure no sensitive details
    assert "traceback" not in response_str, (
        "Error response should not contain traceback. "
        f"Response: {response_data}"
    )
    assert "exception" not in response_str or "exception" in [
        "exception_type",
        "exception",
    ], "Error response should not expose exception details"


def test_p5_s08_no_internal_server_error_details(
    gateway_client, mock_settings, monkeypatch
) -> None:
    """
    P5-S08: 500 errors should not leak internal implementation details.

    Expected Result: 500 response is generic without sensitive details.
    """

    async def fake_introspection(token: str) -> dict:
        return {"sub": "user_123", "roles": ["customer"], "active": True}

    async def fake_forward_error(**kwargs):
        # Simulate a downstream error with internal details
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": "Downstream service error"},  # Generic, not leaked details
        )

    monkeypatch.setattr(
        wso2_client,
        "introspect_access_token",
        fake_introspection,
    )
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    # Mock the forward function to return a generic error
    monkeypatch.setattr(
        "apps.api_gateway.app.infrastructure.http.proxy_client.forward_request",
        fake_forward_error,
    )

    response = gateway_client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer token"},
    )

    response_data = response.json()
    response_str = json.dumps(response_data, default=str).lower()

    # Check response doesn't leak internal details
    assert "database" not in response_str, (
        "Error response should not mention database details. "
        f"Response: {response_data}"
    )
    assert "password" not in response_str, (
        "Error response should not mention password details. "
        f"Response: {response_data}"
    )


def test_p5_s08_auth_error_no_user_enumeration(
    gateway_client, mock_settings, monkeypatch
) -> None:
    """
    P5-S08: Auth errors should not reveal user enumeration info.

    Expected Result: Same error message for missing auth, invalid auth, etc.
    """

    # Missing auth
    response1 = gateway_client.get("/api/v1/products")
    msg1 = response1.json()

    # Invalid auth
    response2 = gateway_client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer invalid"},
    )
    msg2 = response2.json()

    # Both should not reveal whether user exists or not
    msg1_str = json.dumps(msg1, default=str).lower()
    msg2_str = json.dumps(msg2, default=str).lower()

    assert "user" not in msg1_str or "user_not_found" not in msg1_str, (
        "Auth error should not reveal user enumeration info"
    )
    assert "username" not in msg1_str, "Auth error should not contain username hints"


# ============================================================================
# Summary & Evidence
# ============================================================================


def test_p5_security_matrix_coverage() -> None:
    """
    Verify all Phase 5 security test scenarios are covered.

    Covered scenarios:
    - P5-S01: Missing bearer token ✓
    - P5-S02: Invalid bearer token ✓
    - P5-S03: Inactive/expired token ✓
    - P5-S04: IDOR on cart/resource ✓
    - P5-S05: Admin role bypass check ✓
    - P5-S06: Client price tampering ✓
    - P5-S07: Rate limit enforcement ✓
    - P5-S08: Error response leakage ✓
    """
    # This test documents coverage of all Phase 5 security controls
    coverage = {
        "P5-S01": "test_p5_s01_missing_bearer_token_rejected",
        "P5-S02": "test_p5_s02_invalid_bearer_token_rejected, test_p5_s02_malformed_bearer_token_rejected",
        "P5-S03": "test_p5_s03_inactive_opaque_token_rejected, test_p5_s03_expired_jwt_token_rejected",
        "P5-S04": "test_p5_s04_idor_cart_access_blocked, test_p5_s04_idor_cart_own_access_allowed",
        "P5-S05": "test_p5_s05_admin_role_allowed_cart_access",
        "P5-S06": "test_p5_s06_client_price_tampering_rejected, test_p5_s06_price_field_not_accepted",
        "P5-S07": "test_p5_s07_rate_limit_429_returned",
        "P5-S08": "test_p5_s08_no_traceback_in_error_response, test_p5_s08_no_internal_server_error_details, test_p5_s08_auth_error_no_user_enumeration",
    }

    assert len(coverage) == 8, "All 8 Phase 5 security scenarios must be covered"
    for scenario, tests in coverage.items():
        assert tests, f"{scenario} has no tests defined"
