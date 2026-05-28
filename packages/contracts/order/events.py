from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from packages.contracts.common.metadata import BaseEvent, EventType


class OrderCreatedPayload(BaseModel):
    order_id: UUID
    user_id: str
    cart_id: str
    amount: Decimal
    currency: str = "USD"


class OrderCreatedEvent(BaseEvent):
    event_type: EventType = EventType.ORDER_CREATED
    payload: OrderCreatedPayload
