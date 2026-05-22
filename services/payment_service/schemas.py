"""Payment schemas."""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class PaymentResponse(BaseModel):
    payment_id: str
    order_id: str
    user_id: str
    amount: Decimal
    status: str
    created_at: datetime


class PaymentEvent(BaseModel):
    event_id: str
    event_type: str
    order_id: str
    user_id: str
    amount: Decimal
    created_at: datetime