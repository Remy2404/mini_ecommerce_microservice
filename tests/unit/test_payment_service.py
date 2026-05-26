import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from packages.contracts.events import OrderCreatedEvent, OrderCreatedPayload
from services.payment_service.consumers import process_payment


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

    with patch("services.payment_service.consumers.asyncio.sleep", new=AsyncMock()), patch(
        "services.payment_service.consumers.random.random",
        return_value=0,
    ), patch(
        "services.payment_service.consumers.save_payment",
        new=AsyncMock(),
    ) as save_payment_mock, patch(
        "services.payment_service.consumers.broker.publish",
        new=AsyncMock(),
    ) as publish_mock:
        asyncio.run(process_payment(event))

    save_payment_mock.assert_awaited_once()
    saved_payment = save_payment_mock.await_args.kwargs
    assert saved_payment["order_id"] == event.payload.order_id
    assert saved_payment["user_id"] == "user_123"
    assert saved_payment["status"] == "SUCCESS"
    assert saved_payment["amount"] == Decimal("150.00")
    assert saved_payment["failure_reason"] is None
    assert saved_payment["correlation_id"] == event.correlation_id
    publish_mock.assert_awaited_once()


def test_process_payment_persists_failure_before_publishing() -> None:
    event = _order_created_event()

    with patch("services.payment_service.consumers.asyncio.sleep", new=AsyncMock()), patch(
        "services.payment_service.consumers.random.random",
        return_value=1,
    ), patch(
        "services.payment_service.consumers.settings.payment_success_rate",
        0,
    ), patch(
        "services.payment_service.consumers.save_payment",
        new=AsyncMock(),
    ) as save_payment_mock, patch(
        "services.payment_service.consumers.broker.publish",
        new=AsyncMock(),
    ) as publish_mock:
        asyncio.run(process_payment(event))

    save_payment_mock.assert_awaited_once()
    saved_payment = save_payment_mock.await_args.kwargs
    assert saved_payment["order_id"] == event.payload.order_id
    assert saved_payment["user_id"] == "user_123"
    assert saved_payment["status"] == "FAILED"
    assert saved_payment["amount"] == Decimal("150.00")
    assert saved_payment["failure_reason"] == "Simulated payment failure"
    assert saved_payment["correlation_id"] == event.correlation_id
    publish_mock.assert_awaited_once()
