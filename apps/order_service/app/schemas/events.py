from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from apps.order_service.app.schemas.common import PaymentStatus
from apps.order_service.app.schemas.metadata import BaseEvent, EventType


class OrderCreatedPayload(BaseModel):
    order_id: UUID
    user_id: str
    cart_id: str
    amount: Decimal
    currency: str = "USD"


class OrderCreatedEvent(BaseEvent):
    event_type: EventType = EventType.ORDER_CREATED
    payload: OrderCreatedPayload


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


class PaymentSuccessEvent(BaseEvent):
    event_type: EventType = EventType.PAYMENT_SUCCESS
    payload: PaymentSuccessPayload


class PaymentFailedEvent(BaseEvent):
    event_type: EventType = EventType.PAYMENT_FAILED
    payload: PaymentFailedPayload
