from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(StrEnum):
    ORDER_CREATED = "order.created"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_CANCELLED = "order.cancelled"
    CART_RESTORED = "cart.restored"


class PaymentStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4()}")
    event_type: EventType
    trace_id: str | None = None
    correlation_id: str = Field(default_factory=lambda: f"corr_{uuid4()}")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrderCreatedPayload(BaseModel):
    order_id: UUID
    user_id: str
    cart_id: str
    amount: Decimal
    currency: str = "USD"


class PaymentSuccessPayload(BaseModel):
    payment_id: UUID
    order_id: UUID
    user_id: str
    amount: Decimal
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.SUCCESS


class PaymentFailedPayload(BaseModel):
    payment_id: UUID
    order_id: UUID
    user_id: str
    amount: Decimal
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.FAILED
    reason: str


class OrderCreatedEvent(BaseEvent):
    event_type: EventType = EventType.ORDER_CREATED
    payload: OrderCreatedPayload


class PaymentSuccessEvent(BaseEvent):
    event_type: EventType = EventType.PAYMENT_SUCCESS
    payload: PaymentSuccessPayload


class PaymentFailedEvent(BaseEvent):
    event_type: EventType = EventType.PAYMENT_FAILED
    payload: PaymentFailedPayload


EventPayload = OrderCreatedPayload | PaymentSuccessPayload | PaymentFailedPayload

DomainEvent = OrderCreatedEvent | PaymentSuccessEvent | PaymentFailedEvent
