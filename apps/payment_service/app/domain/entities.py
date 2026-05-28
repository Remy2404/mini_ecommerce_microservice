"""Pure payment domain entities."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class PaymentEntity:
    payment_id: UUID
    order_id: UUID
    user_id: str
    amount: Decimal
    currency: str
    status: str
