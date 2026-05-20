from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import json
import pytest

from packages.contracts.events import (
    EventType,
    PaymentStatus,
    OrderCreatedEvent,
    OrderCreatedPayload,
    PaymentSuccessEvent,
    PaymentSuccessPayload,
    PaymentFailedEvent,
    PaymentFailedPayload,
)

@pytest.fixture
def common_ids():
    return {
        "order_id": uuid4(),
        "user_id": "user_ramy_99",
        "cart_id": "cart_123",
        "payment_id": uuid4(),
    }

@pytest.mark.parametrize(
    "event_class, payload_class, event_type, extra_payload",
    [
        (
            OrderCreatedEvent,
            OrderCreatedPayload,
            EventType.ORDER_CREATED,
            {"cart_id": "cart_123"},
        ),
        (
            PaymentSuccessEvent,
            PaymentSuccessPayload,
            EventType.PAYMENT_SUCCESS,
            {"payment_id": uuid4(), "status": PaymentStatus.SUCCESS},
        ),
        (
            PaymentFailedEvent,
            PaymentFailedPayload,
            EventType.PAYMENT_FAILED,
            {
                "payment_id": uuid4(),
                "status": PaymentStatus.FAILED,
                "reason": "Insufficient Funds",
            },
        ),
    ],
)
def test_domain_events_serialization(
    event_class, payload_class, event_type, extra_payload, common_ids
):
    # Arrange:
    base_payload_data = {
        "order_id": common_ids["order_id"],
        "user_id": common_ids["user_id"],
        "amount": Decimal("150.50"),
        "currency": "USD",
    }
    base_payload_data.update(extra_payload)
    payload = payload_class(**base_payload_data)

    event = event_class(payload=payload, trace_id="trace_abc123")
    json_str = event.model_dump_json()
    data = json.loads(json_str)

    assert data["event_id"].startswith("evt_")
    assert data["correlation_id"].startswith("corr_")
    assert data["event_type"] == event_type.value
    assert data["trace_id"] == "trace_abc123"

    occurred_at = datetime.fromisoformat(data["occurred_at"])
    assert occurred_at.tzinfo == timezone.utc

   
    assert data["payload"]["user_id"] == common_ids["user_id"]
    assert (
        data["payload"]["amount"] == "150.50"
    )  

    if "reason" in extra_payload:
        assert data["payload"]["reason"] == "Insufficient Funds"
