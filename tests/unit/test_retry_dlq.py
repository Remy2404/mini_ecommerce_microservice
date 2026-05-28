import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from packages.contracts.events import OrderCreatedEvent, OrderCreatedPayload
from packages.contracts.order.topics import RoutingKey
from packages.messaging.retry import publish_retry_or_dlq, retry_decision


def test_retry_decision_uses_retry_before_max_attempts(monkeypatch) -> None:
    from packages.config.settings import settings

    monkeypatch.setattr(settings, "rabbitmq_retry_max_attempts", 3)
    decision = retry_decision(
        current_retry_count=0,
        retry_routing_key=RoutingKey.ORDER_CREATED_RETRY,
        dlq_routing_key=RoutingKey.ORDER_CREATED_DLQ,
    )

    assert decision.should_retry is True
    assert decision.next_retry_count == 1
    assert decision.routing_key == RoutingKey.ORDER_CREATED_RETRY


def test_retry_decision_routes_poison_message_to_dlq(monkeypatch) -> None:
    from packages.config.settings import settings

    monkeypatch.setattr(settings, "rabbitmq_retry_max_attempts", 3)
    decision = retry_decision(
        current_retry_count=3,
        retry_routing_key=RoutingKey.ORDER_CREATED_RETRY,
        dlq_routing_key=RoutingKey.ORDER_CREATED_DLQ,
    )

    assert decision.should_retry is False
    assert decision.next_retry_count == 4
    assert decision.routing_key == RoutingKey.ORDER_CREATED_DLQ


def test_publish_retry_or_dlq_publishes_retry_metadata(monkeypatch) -> None:
    from packages.messaging import retry as retry_module

    event = OrderCreatedEvent(
        payload=OrderCreatedPayload(
            order_id=uuid4(),
            user_id="user_123",
            cart_id="cart_user_123",
            amount=Decimal("25.00"),
        )
    )

    publish_mock = AsyncMock()
    monkeypatch.setattr(retry_module.broker, "publish", publish_mock)

    decision = asyncio.run(
        publish_retry_or_dlq(
            event=event,
            error=RuntimeError("provider timeout"),
            retry_routing_key=RoutingKey.ORDER_CREATED_RETRY,
            dlq_routing_key=RoutingKey.ORDER_CREATED_DLQ,
            service_name="payment-service",
        )
    )

    assert decision.should_retry is True
    publish_mock.assert_awaited_once()
    kwargs = publish_mock.await_args.kwargs
    assert kwargs["routing_key"] == RoutingKey.ORDER_CREATED_RETRY
    assert kwargs["message"]["retry_count"] == 1
    assert kwargs["message"]["last_error"] == "provider timeout"


def test_payment_consumer_failure_routes_to_dlq_after_retries(monkeypatch) -> None:
    from apps.payment_service.app.infrastructure.messaging.order_created_consumer import (
        process_payment,
    )
    from packages.config.settings import settings

    event = OrderCreatedEvent(
        retry_count=3,
        payload=OrderCreatedPayload(
            order_id=uuid4(),
            user_id="user_123",
            cart_id="cart_user_123",
            amount=Decimal("25.00"),
        ),
    )

    monkeypatch.setattr(settings, "rabbitmq_retry_max_attempts", 3)

    with (
        patch(
            "apps.payment_service.app.infrastructure.messaging.order_created_consumer.acquire_payment_event_lock",
            new=AsyncMock(side_effect=RuntimeError("lock backend down")),
        ),
        patch(
            "packages.messaging.retry.broker.publish",
            new=AsyncMock(),
        ) as publish_mock,
    ):
        asyncio.run(process_payment(event))

    publish_mock.assert_awaited_once()
    assert publish_mock.await_args.kwargs["routing_key"] == RoutingKey.ORDER_CREATED_DLQ
