"""Shared API and event contracts for the mini-ecommerce services."""

from ecommerce_contracts.common.metadata import BaseEvent, EventType
from ecommerce_contracts.events import (
    DomainEvent,
    EventPayload,
    OrderCreatedEvent,
    OrderCreatedPayload,
    PaymentFailedEvent,
    PaymentFailedPayload,
    PaymentStatus,
    PaymentSuccessEvent,
    PaymentSuccessPayload,
)
from ecommerce_contracts.schemas import (
    ApiErrorResponse,
    ApiResponse,
    CartItem,
    CartResponse,
    OrderItem,
    OrderResponse,
    OrderStatus,
    PaymentResponse,
    ProductResponse,
)
from ecommerce_contracts.topics import ExchangeName, QueueName, RoutingKey

__all__ = [
    "ApiErrorResponse",
    "ApiResponse",
    "BaseEvent",
    "CartItem",
    "CartResponse",
    "DomainEvent",
    "EventPayload",
    "EventType",
    "ExchangeName",
    "OrderCreatedEvent",
    "OrderCreatedPayload",
    "OrderItem",
    "OrderResponse",
    "OrderStatus",
    "PaymentFailedEvent",
    "PaymentFailedPayload",
    "PaymentResponse",
    "PaymentStatus",
    "PaymentSuccessEvent",
    "PaymentSuccessPayload",
    "ProductResponse",
    "QueueName",
    "RoutingKey",
]

