from packages.contracts.common.metadata import BaseEvent, EventType
from packages.contracts.order.events import OrderCreatedEvent, OrderCreatedPayload
from packages.contracts.payment.events import (
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
