"""E2E tests for core user flows: login and checkout."""

import asyncio
from decimal import Decimal
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.api_gateway.app.infrastructure.http import proxy_client as proxy
from apps.api_gateway.app.infrastructure.security import wso2_client
from apps.api_gateway.app.main import app as gateway_app
from apps.auth_service.app.application.services import AuthService
from apps.auth_service.app.schemas.requests import RegisterUserRequest
from apps.cart_service.app.application import services as cart_services
from apps.cart_service.app.schemas import AddCartItemRequest, CartResponse
from apps.order_service.app.application import services as order_services
from apps.order_service.app.infrastructure.clients.cart_client import (
    CartSnapshot,
    CartSnapshotItem,
)
from apps.product_service.app.schemas import ProductResponse
from packages.config.settings import settings


# ========== Test Data ==========
class TestData:
    """Deterministic test data for E2E flows."""

    BUYER_USERNAME = "test_buyer"
    BUYER_EMAIL = "test_buyer@example.com"
    BUYER_PASSWORD = "SecureTestPassword123!"
    BUYER_FIRST_NAME = "Test"
    BUYER_LAST_NAME = "Buyer"

    INVALID_PASSWORD = "wrong_password"

    PRODUCT_ID = uuid4()
    PRODUCT_NAME = "Test Laptop"
    PRODUCT_PRICE = Decimal("999.99")
    PRODUCT_STOCK = 10
    PRODUCT_CATEGORY = "electronics"

    CART_ITEM_QUANTITY = 2


# ========== Fixtures and Helpers ==========
class FakeGatewayAsyncClient:
    """Mock async HTTP client for gateway."""

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


async def async_noop(*args, **kwargs) -> None:
    """No-op async function."""
    return None


async def return_async(value):
    """Return value asynchronously."""
    return value


# ========== P4-E01: User Login Flow (Valid Credentials) ==========
def test_e2e_login_with_valid_credentials(monkeypatch) -> None:
    """
    P4-E01: User login flow - Verify successful login with valid credentials.

    Preconditions: Test user exists in WSO2
    Main Steps: Open login > submit valid credentials
    Expected Result: Redirect/dashboard visible (token returned)
    """

    async def fake_wso2_password_token(
        username: str, password: str, scope: str
    ) -> dict:
        """Mock successful password grant flow."""
        assert username == TestData.BUYER_USERNAME
        assert password == TestData.BUYER_PASSWORD
        return {
            "access_token": "mock-access-token-12345",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": scope,
        }

    # Patch at the route handler level
    monkeypatch.setattr(
        "apps.api_gateway.app.api.routes.auth_routes.request_wso2_password_token",
        fake_wso2_password_token,
    )

    with TestClient(gateway_app) as client:
        response = client.post(
            "/internal/wso2/login",
            json={
                "username": TestData.BUYER_USERNAME,
                "password": TestData.BUYER_PASSWORD,
                "scope": "read write",
            },
        )

    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "Bearer"
    assert token_data["expires_in"] == 3600


# ========== P4-E02: User Login Flow (Invalid Credentials) ==========
def test_e2e_login_with_invalid_credentials(monkeypatch) -> None:
    """
    P4-E02: User login invalid - Verify error handling for invalid credentials.

    Preconditions: Test user exists
    Main Steps: Submit invalid credentials
    Expected Result: Error shown, no login
    """

    async def fake_wso2_password_token_error(
        username: str, password: str, scope: str
    ) -> dict:
        """Mock failed password grant flow."""
        raise ValueError("Invalid credentials")

    monkeypatch.setattr(
        "apps.api_gateway.app.api.routes.auth_routes.request_wso2_password_token",
        fake_wso2_password_token_error,
    )

    with TestClient(gateway_app) as client:
        response = client.post(
            "/internal/wso2/login",
            json={
                "username": TestData.BUYER_USERNAME,
                "password": TestData.INVALID_PASSWORD,
                "scope": "read write",
            },
        )

    assert response.status_code in [400, 401, 422, 500]


# ========== P4-E03: Browse Products ==========
def test_e2e_browse_products_catalog(monkeypatch) -> None:
    """
    P4-E03: Browse products - Verify product list can be retrieved.

    Preconditions: Seed products available
    Main Steps: Open catalog and filter/select item
    Expected Result: Product list/detail loads correctly
    """

    async def fake_introspection(token: str) -> dict:
        """Mock token introspection."""
        return {"sub": "user_123", "roles": ["customer"], "active": True}

    async def fake_proxy_request(method, url, **kwargs):
        """Mock product service response."""
        if "/products" in url:
            return httpx.Response(
                200,
                json=[
                    {
                        "product_id": str(TestData.PRODUCT_ID),
                        "name": TestData.PRODUCT_NAME,
                        "description": "High performance laptop",
                        "price": str(TestData.PRODUCT_PRICE),
                        "stock_quantity": TestData.PRODUCT_STOCK,
                        "category": TestData.PRODUCT_CATEGORY,
                    }
                ],
            )
        return httpx.Response(200, json={})

    FakeGatewayAsyncClient.calls = []
    FakeGatewayAsyncClient.response = httpx.Response(
        200,
        json=[
            {
                "product_id": str(TestData.PRODUCT_ID),
                "name": TestData.PRODUCT_NAME,
                "description": "High performance laptop",
                "price": str(TestData.PRODUCT_PRICE),
                "stock_quantity": TestData.PRODUCT_STOCK,
                "category": TestData.PRODUCT_CATEGORY,
            }
        ],
    )

    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeGatewayAsyncClient)
    monkeypatch.setattr(wso2_client, "introspect_access_token", fake_introspection)
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")

    with TestClient(gateway_app) as client:
        response = client.get(
            "/api/v1/products",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    products = response.json()
    assert len(products) > 0
    assert products[0]["name"] == TestData.PRODUCT_NAME
    assert products[0]["category"] == TestData.PRODUCT_CATEGORY


# ========== P4-E04: Add Item to Cart ==========
def test_e2e_add_item_to_cart(monkeypatch) -> None:
    """
    P4-E04: Add item to cart - Verify cart operations work correctly.

    Preconditions: Logged-in user
    Main Steps: Select product > add to cart
    Expected Result: Cart count/line item updates
    """

    user_id = "test-user-123"

    # Create a trusted product
    trusted_product = ProductResponse(
        product_id=TestData.PRODUCT_ID,
        name=TestData.PRODUCT_NAME,
        description="High performance laptop",
        price=TestData.PRODUCT_PRICE,
        stock_quantity=TestData.PRODUCT_STOCK,
        category=TestData.PRODUCT_CATEGORY,
    )

    saved_carts = []

    # Mock cart service functions
    monkeypatch.setattr(
        cart_services, "fetch_product", lambda _: return_async(trusted_product)
    )
    monkeypatch.setattr(
        cart_services,
        "get_cart",
        lambda uid: CartResponse(user_id=uid, items=[], total_amount=Decimal("0")),
    )
    monkeypatch.setattr(cart_services, "save_cart", saved_carts.append)

    # Add item to cart
    asyncio.run(
        cart_services.add_item_to_cart(
            user_id,
            AddCartItemRequest(
                product_id=TestData.PRODUCT_ID,
                quantity=TestData.CART_ITEM_QUANTITY,
            ),
        )
    )

    # Verify cart was updated
    assert len(saved_carts) > 0
    assert saved_carts[0].user_id == user_id
    assert len(saved_carts[0].items) == 1
    assert saved_carts[0].items[0].quantity == TestData.CART_ITEM_QUANTITY
    assert saved_carts[0].items[0].unit_price == TestData.PRODUCT_PRICE
    assert (
        saved_carts[0].total_amount
        == TestData.PRODUCT_PRICE * TestData.CART_ITEM_QUANTITY
    )


# ========== P4-E05: Checkout/Order Creation ==========
def test_e2e_checkout_and_order_creation(monkeypatch) -> None:
    """
    P4-E05: Checkout/order creation - Verify complete order flow.

    Preconditions: Cart has item
    Main Steps: Proceed checkout > confirm order
    Expected Result: Order created and confirmation shown
    """

    user_id = "test-user-123"

    # Setup cart snapshot
    cart_snapshot = CartSnapshot(
        cart_id=f"cart_{user_id}",
        total_amount=TestData.PRODUCT_PRICE * TestData.CART_ITEM_QUANTITY,
        items=[
            CartSnapshotItem(
                product_id=TestData.PRODUCT_ID,
                product_name=TestData.PRODUCT_NAME,
                quantity=TestData.CART_ITEM_QUANTITY,
                unit_price=TestData.PRODUCT_PRICE,
                subtotal=TestData.PRODUCT_PRICE * TestData.CART_ITEM_QUANTITY,
            )
        ],
    )

    # Mock order service functions
    monkeypatch.setattr(
        order_services,
        "get_cart_snapshot",
        lambda uid: cart_snapshot,
    )
    monkeypatch.setattr(order_services, "save_order_with_outbox", async_noop)
    monkeypatch.setattr(order_services, "publish_pending_order_events", async_noop)

    # Create order
    order = asyncio.run(order_services.create_order_for_user(user_id))

    # Verify order was created
    assert order is not None
    assert order.order_id is not None
    assert order.status == "PENDING"


# ========== P4-E06: Smoke Health Verification ==========
def test_e2e_smoke_health_verification() -> None:
    """
    P4-E06: Smoke health verification - Verify critical services are healthy.

    Preconditions: Services running
    Main Steps: Trigger smoke checks
    Expected Result: Critical services healthy
    """

    # Test gateway health
    with TestClient(gateway_app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "api-gateway"


# ========== Complete E2E Checkout Flow ==========
def test_e2e_complete_user_journey_login_to_order(monkeypatch) -> None:
    """
    Complete E2E flow: User Registration -> Browse Products -> Add to Cart -> Checkout.

    This is a comprehensive integration test covering all major user interactions.
    """

    auth_service = AuthService()
    user_id = "journey-user-123"

    # Step 1: User Registration
    async def fake_register_wso2_user(
        *,
        username: str,
        email: str,
        password: str,
        given_name: str,
        family_name: str,
        request_id: str | None = None,
    ):
        assert username == TestData.BUYER_USERNAME
        assert email == TestData.BUYER_EMAIL
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "message": "User registered successfully",
        }

    monkeypatch.setattr(
        "apps.auth_service.app.application.services.register_wso2_user",
        fake_register_wso2_user,
    )

    registered = asyncio.run(
        auth_service.register_user(
            RegisterUserRequest(
                username=TestData.BUYER_USERNAME,
                email=TestData.BUYER_EMAIL,
                password=SecretStr(TestData.BUYER_PASSWORD),
                first_name=TestData.BUYER_FIRST_NAME,
                last_name=TestData.BUYER_LAST_NAME,
            )
        )
    )

    assert registered.id == user_id

    # Step 2: Browse Products (already verified in P4-E03)
    trusted_product = ProductResponse(
        product_id=TestData.PRODUCT_ID,
        name=TestData.PRODUCT_NAME,
        description="High performance laptop",
        price=TestData.PRODUCT_PRICE,
        stock_quantity=TestData.PRODUCT_STOCK,
        category=TestData.PRODUCT_CATEGORY,
    )

    saved_carts = []
    monkeypatch.setattr(
        cart_services, "fetch_product", lambda _: return_async(trusted_product)
    )
    monkeypatch.setattr(
        cart_services,
        "get_cart",
        lambda uid: CartResponse(user_id=uid, items=[], total_amount=Decimal("0")),
    )
    monkeypatch.setattr(cart_services, "save_cart", saved_carts.append)

    # Step 3: Add Product to Cart
    cart = asyncio.run(
        cart_services.add_item_to_cart(
            registered.id,
            AddCartItemRequest(
                product_id=TestData.PRODUCT_ID,
                quantity=TestData.CART_ITEM_QUANTITY,
            ),
        )
    )

    assert len(saved_carts) > 0
    assert saved_carts[0].total_amount == Decimal("1999.98")

    # Step 4: Checkout and Create Order
    monkeypatch.setattr(
        order_services,
        "get_cart_snapshot",
        lambda uid: CartSnapshot(
            cart_id=f"cart_{uid}",
            total_amount=cart.total_amount,
            items=[
                CartSnapshotItem(
                    product_id=cart.items[0].product_id,
                    product_name=cart.items[0].name,
                    quantity=cart.items[0].quantity,
                    unit_price=cart.items[0].unit_price,
                    subtotal=cart.items[0].subtotal,
                )
            ],
        ),
    )
    monkeypatch.setattr(order_services, "save_order_with_outbox", async_noop)
    monkeypatch.setattr(order_services, "publish_pending_order_events", async_noop)

    order = asyncio.run(order_services.create_order_for_user(registered.id))

    # Final Verification
    assert order.status == "PENDING"
    assert order.order_id is not None
