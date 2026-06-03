from ecommerce_contracts.common.metadata import BaseEvent, EventType
from ecommerce_contracts.order.events import OrderCreatedEvent, OrderCreatedPayload
from ecommerce_contracts.payment.events import (
    PaymentFailedEvent,
    PaymentFailedPayload,
    PaymentStatus,
    PaymentSuccessEvent,
    PaymentSuccessPayload,
)

EventPayload = OrderCreatedPayload | PaymentSuccessPayload | PaymentFailedPayload
DomainEvent = OrderCreatedEvent | PaymentSuccessEvent | PaymentFailedEvent

__all__ = [
    "BaseEvent",
    "DomainEvent",
    "EventPayload",
    "EventType",
    "OrderCreatedEvent",
    "OrderCreatedPayload",
    "PaymentFailedEvent",
    "PaymentFailedPayload",
    "PaymentStatus",
    "PaymentSuccessEvent",
    "PaymentSuccessPayload",
]

