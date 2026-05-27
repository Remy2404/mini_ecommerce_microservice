import asyncio
from decimal import Decimal
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.api_gateway.app.infrastructure.http import proxy_client as proxy
from apps.api_gateway.app.main import app as gateway_app
from apps.auth_service.app.application.services import AuthService
from apps.auth_service.app.schemas.requests import LoginRequest, RegisterUserRequest
from apps.cart_service.app.application import services as cart_services
from apps.cart_service.app.schemas import AddCartItemRequest, CartResponse
from apps.order_service.app.application import services as order_services
from apps.order_service.app.infrastructure.clients.cart_client import CartSnapshot, CartSnapshotItem
from apps.order_service.app.infrastructure.messaging.payment_result_consumer import handle_payment_result
from apps.payment_service.app.infrastructure.messaging.order_created_consumer import process_payment
from apps.product_service.app.schemas import ProductResponse
from packages.config.settings import settings
from packages.contracts.events import (
    OrderCreatedEvent,
    OrderCreatedPayload,
    PaymentFailedEvent,
    PaymentFailedPayload,
    PaymentSuccessEvent,
    PaymentSuccessPayload,
)
from packages.security.jwt import create_access_token
from packages.security.passwords import hash_password


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


class FakeGatewayAsyncClient:
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


def test_e2e_user_register_login_product_cart_and_order(monkeypatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret_key", SecretStr("x" * 32))
    auth_service = AuthService(repository=FakeAuthRepository())

    registered = asyncio.run(
        auth_service.register_user(
            RegisterUserRequest(
                email="buyer@example.com",
                password=SecretStr("strong-password"),
                full_name="Buyer",
            )
        )
    )
    login = asyncio.run(
        auth_service.login_user(
            LoginRequest(email="buyer@example.com", password=SecretStr("strong-password"))
        )
    )

    product_id = uuid4()
    trusted_product = ProductResponse(
        product_id=product_id,
        name="Trusted Product",
        description=None,
        price=Decimal("15.00"),
        stock_quantity=8,
        category="books",
    )
    saved_carts = []

    monkeypatch.setattr(cart_services, "fetch_product", lambda _: _return_async(trusted_product))
    monkeypatch.setattr(
        cart_services,
        "get_cart",
        lambda user_id: CartResponse(user_id=user_id, items=[], total_amount=Decimal("0")),
    )
    monkeypatch.setattr(cart_services, "save_cart", saved_carts.append)

    cart = asyncio.run(
        cart_services.add_item_to_cart(
            AddCartItemRequest(
                user_id=str(registered.user_id),
                product_id=product_id,
                quantity=2,
            )
        )
    )

    monkeypatch.setattr(
        order_services,
        "get_cart_snapshot",
        lambda user_id: CartSnapshot(
            cart_id=f"cart_{user_id}",
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
    monkeypatch.setattr(order_services, "save_order_with_outbox", _async_noop)
    monkeypatch.setattr(order_services, "publish_pending_order_events", _async_noop)

    order = asyncio.run(order_services.create_order_for_user(str(registered.user_id)))

    assert login.access_token
    assert saved_carts[0].items[0].unit_price == Decimal("15.00")
    assert saved_carts[0].total_amount == Decimal("30.00")
    assert order.status == "PENDING"


def test_e2e_payment_success_updates_order_and_clears_cart(monkeypatch) -> None:
    payment_id = uuid4()
    order_id = uuid4()
    updated_statuses = []

    monkeypatch.setattr(
        "apps.order_service.app.infrastructure.messaging.payment_result_consumer.apply_payment_result_once",
        lambda event_id, event_type, order_id, status: _return_and_record_async(
            updated_statuses,
            (str(order_id), status),
            True,
        ),
    )

    class FakeValkey:
        deleted = []

        def delete(self, key):
            self.deleted.append(key)

    fake_valkey = FakeValkey()
    monkeypatch.setattr(
        "apps.order_service.app.infrastructure.messaging.payment_result_consumer.get_valkey_client",
        lambda: fake_valkey,
    )

    event = PaymentSuccessEvent(
        payload=PaymentSuccessPayload(
            payment_id=payment_id,
            order_id=order_id,
            user_id="user_123",
            amount=Decimal("30.00"),
        )
    )

    asyncio.run(handle_payment_result(event))

    assert updated_statuses == [(str(order_id), "CONFIRMED")]
    assert fake_valkey.deleted == ["cart:user_123"]


def test_e2e_payment_failure_updates_order_and_keeps_cart(monkeypatch) -> None:
    payment_id = uuid4()
    order_id = uuid4()
    updated_statuses = []

    monkeypatch.setattr(
        "apps.order_service.app.infrastructure.messaging.payment_result_consumer.apply_payment_result_once",
        lambda event_id, event_type, order_id, status: _return_and_record_async(
            updated_statuses,
            (str(order_id), status),
            True,
        ),
    )

    class FakeValkey:
        deleted = []

        def delete(self, key):
            self.deleted.append(key)

    fake_valkey = FakeValkey()
    monkeypatch.setattr(
        "apps.order_service.app.infrastructure.messaging.payment_result_consumer.get_valkey_client",
        lambda: fake_valkey,
    )

    event = PaymentFailedEvent(
        payload=PaymentFailedPayload(
            payment_id=payment_id,
            order_id=order_id,
            user_id="user_123",
            amount=Decimal("30.00"),
            reason="Simulated payment failure",
        )
    )

    asyncio.run(handle_payment_result(event))

    assert updated_statuses == [(str(order_id), "CANCELLED")]
    assert fake_valkey.deleted == []


def test_e2e_payment_worker_persists_outbox_and_publishes(monkeypatch) -> None:
    saved = []
    published_batches = []
    event = OrderCreatedEvent(
        payload=OrderCreatedPayload(
            order_id=uuid4(),
            user_id="user_123",
            cart_id="cart_user_123",
            amount=Decimal("30.00"),
        )
    )

    monkeypatch.setattr(
        "apps.payment_service.app.infrastructure.messaging.order_created_consumer.acquire_payment_event_lock",
        lambda event_id: _return_async(True),
    )
    monkeypatch.setattr(
        "apps.payment_service.app.infrastructure.messaging.order_created_consumer.asyncio.sleep",
        lambda delay: _return_async(None),
    )
    monkeypatch.setattr(
        "apps.payment_service.app.infrastructure.messaging.order_created_consumer.save_payment_with_outbox_once",
        lambda **kwargs: _return_and_record_async(saved, kwargs, True),
    )
    monkeypatch.setattr(
        "apps.payment_service.app.infrastructure.messaging.order_created_consumer.publish_pending_payment_events",
        lambda limit: _return_and_record_async(published_batches, limit, 1),
    )
    monkeypatch.setattr(settings, "payment_success_rate", 1.0)

    asyncio.run(process_payment(event))

    assert saved[0]["status"] == "SUCCESS"
    assert saved[0]["routing_key"] == "payment.succeeded.v1"
    assert published_batches == [10]


def test_e2e_gateway_route_metrics_and_auth(monkeypatch) -> None:
    FakeGatewayAsyncClient.calls = []
    monkeypatch.setattr(proxy.httpx, "AsyncClient", FakeGatewayAsyncClient)
    monkeypatch.setattr(settings, "gateway_auth_enabled", True)
    monkeypatch.setattr(settings, "gateway_rate_limit_enabled", False)
    monkeypatch.setattr(settings, "jwt_secret_key", SecretStr("x" * 32))
    monkeypatch.setattr(settings, "product_service_url", "http://product-service")

    token = create_access_token(subject="user_123", roles=["customer"])

    with TestClient(gateway_app) as client:
        protected = client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {token}"},
        )
        metrics = client.get("/metrics")

    assert protected.status_code == 200
    assert FakeGatewayAsyncClient.calls[0]["url"] == "http://product-service/products"
    assert metrics.status_code == 200
    assert "http_request_total" in metrics.text


async def _async_noop(*args, **kwargs) -> None:
    return None


async def _record_async(target: list, value) -> None:
    target.append(value)


async def _return_and_record_async(target: list, value, return_value):
    target.append(value)
    return return_value


async def _return_async(value):
    return value
