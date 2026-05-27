from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(StrEnum):
    ORDER_CREATED = "order.created"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_CANCELLED = "order.cancelled"
    CART_RESTORED = "cart.restored"


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4()}")
    event_type: EventType
    trace_id: str | None = None
    correlation_id: str = Field(default_factory=lambda: f"corr_{uuid4()}")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
