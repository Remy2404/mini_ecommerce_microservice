from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from packages.contracts.common.metadata import BaseEvent, EventType


class PaymentStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


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
