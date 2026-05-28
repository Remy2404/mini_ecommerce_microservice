import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from packages.contracts.events import OrderCreatedEvent, OrderCreatedPayload
from apps.payment_service.app.infrastructure.messaging.order_created_consumer import process_payment


def _order_created_event() -> OrderCreatedEvent:
    return OrderCreatedEvent(
        payload=OrderCreatedPayload(
            order_id=uuid4(),
            user_id="user_123",
            cart_id="cart_user_123",
            amount=Decimal("150.00"),
        )
    )


def test_process_payment_persists_success_before_publishing() -> None:
    event = _order_created_event()

    with (
        patch("apps.payment_service.app.infrastructure.messaging.order_created_consumer.asyncio.sleep", new=AsyncMock()),
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.random.random",
            return_value=0,
        ),
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.save_payment_with_outbox_once",
            new=AsyncMock(return_value=True),
        ) as save_payment_with_outbox_mock,
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.publish_pending_payment_events",
            new=AsyncMock(),
        ) as publish_pending_mock,
    ):
        asyncio.run(process_payment(event))

    save_payment_with_outbox_mock.assert_awaited_once()
    saved_payment = save_payment_with_outbox_mock.await_args.kwargs
    assert saved_payment["order_id"] == event.payload.order_id
    assert saved_payment["user_id"] == "user_123"
    assert saved_payment["status"] == "SUCCESS"
    assert saved_payment["amount"] == Decimal("150.00")
    assert saved_payment["failure_reason"] is None
    assert saved_payment["correlation_id"] == event.correlation_id
    assert saved_payment["source_event_id"] == event.event_id
    assert saved_payment["routing_key"] == "payment.succeeded.v1"
    publish_pending_mock.assert_awaited_once()


def test_process_payment_persists_failure_before_publishing() -> None:
    event = _order_created_event()

    with (
        patch("apps.payment_service.app.infrastructure.messaging.order_created_consumer.asyncio.sleep", new=AsyncMock()),
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.random.random",
            return_value=1,
        ),
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.settings.payment_success_rate",
            0,
        ),
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.save_payment_with_outbox_once",
            new=AsyncMock(return_value=True),
        ) as save_payment_with_outbox_mock,
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.publish_pending_payment_events",
            new=AsyncMock(),
        ) as publish_pending_mock,
    ):
        asyncio.run(process_payment(event))

    save_payment_with_outbox_mock.assert_awaited_once()
    saved_payment = save_payment_with_outbox_mock.await_args.kwargs
    assert saved_payment["order_id"] == event.payload.order_id
    assert saved_payment["user_id"] == "user_123"
    assert saved_payment["status"] == "FAILED"
    assert saved_payment["amount"] == Decimal("150.00")
    assert saved_payment["failure_reason"] == "Simulated payment failure"
    assert saved_payment["correlation_id"] == event.correlation_id
    assert saved_payment["source_event_id"] == event.event_id
    assert saved_payment["routing_key"] == "payment.failed.v1"
    publish_pending_mock.assert_awaited_once()
