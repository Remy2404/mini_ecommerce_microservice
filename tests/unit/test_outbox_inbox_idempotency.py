import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from packages.contracts.events import (
    OrderCreatedEvent,
    OrderCreatedPayload,
    PaymentSuccessEvent,
    PaymentSuccessPayload,
)


def test_order_consumer_skips_duplicate_payment_result_without_clearing_cart() -> None:
    from apps.order_service.app.infrastructure.messaging.payment_result_consumer import (
        handle_payment_result,
    )

    event = PaymentSuccessEvent(
        payload=PaymentSuccessPayload(
            payment_id=uuid4(),
            order_id=uuid4(),
            user_id="user_123",
            amount=Decimal("25.00"),
        )
    )

    class FakeValkey:
        def __init__(self) -> None:
            self.deleted: list[str] = []

        def delete(self, key: str) -> None:
            self.deleted.append(key)

    fake_valkey = FakeValkey()

    with (
        patch(
            "apps.order_service.app.infrastructure.messaging.payment_result_consumer.apply_payment_result_once",
            new=AsyncMock(side_effect=[True, False]),
        ) as apply_once,
        patch(
            "apps.order_service.app.infrastructure.messaging.payment_result_consumer.get_valkey_client",
            return_value=fake_valkey,
        ),
    ):
        asyncio.run(handle_payment_result(event))
        asyncio.run(handle_payment_result(event))

    assert apply_once.await_count == 2
    assert fake_valkey.deleted == ["cart:user_123"]


def test_payment_consumer_skips_duplicate_order_created_after_inbox_record() -> None:
    from apps.payment_service.app.infrastructure.messaging.order_created_consumer import (
        process_payment,
    )

    event = OrderCreatedEvent(
        payload=OrderCreatedPayload(
            order_id=uuid4(),
            user_id="user_123",
            cart_id="cart_user_123",
            amount=Decimal("25.00"),
        )
    )

    with (
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.acquire_payment_event_lock",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.asyncio.sleep",
            new=AsyncMock(),
        ),
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.random.random",
            return_value=0,
        ),
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.save_payment_with_outbox_once",
            new=AsyncMock(side_effect=[True, False]),
        ) as save_once,
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.publish_pending_payment_events",
            new=AsyncMock(),
        ) as publish_pending,
    ):
        asyncio.run(process_payment(event))
        asyncio.run(process_payment(event))

    assert save_once.await_count == 2
    publish_pending.assert_awaited_once()
