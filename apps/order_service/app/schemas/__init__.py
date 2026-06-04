"""Order Service request and response DTOs."""

from apps.order_service.app.schemas.common import (
    ApiResponse,
    CartSnapshot,
    CartSnapshotItem,
    OrderItemResponse,
    OrderStatus,
    OrderSummaryResponse,
)
from apps.order_service.app.schemas.events import OrderCreatedEvent, OrderCreatedPayload
from apps.order_service.app.schemas.requests import CreateOrderRequest
from apps.order_service.app.schemas.responses import (
    OrderItemResponse as LegacyOrderItemResponse,
    OrderSummaryResponse as LegacyOrderSummaryResponse,
)
from apps.order_service.app.schemas.topics import ExchangeName, QueueName, RoutingKey

__all__ = [
    "ApiResponse",
    "CartSnapshot",
    "CartSnapshotItem",
    "CreateOrderRequest",
    "ExchangeName",
    "LegacyOrderItemResponse",
    "LegacyOrderSummaryResponse",
    "OrderCreatedEvent",
    "OrderCreatedPayload",
    "OrderItemResponse",
    "OrderStatus",
    "OrderSummaryResponse",
    "QueueName",
    "RoutingKey",
]

