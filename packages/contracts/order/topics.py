from enum import StrEnum


class ExchangeName(StrEnum):
    ECOMMERCE = "ecommerce.exchange"


class RoutingKey(StrEnum):
    ORDER_CREATED = "order.created.v1"
    PAYMENT_SUCCESS = "payment.succeeded.v1"
    PAYMENT_FAILED = "payment.failed.v1"
    ORDER_CONFIRMED = "order.confirmed.v1"
    ORDER_CANCELLED = "order.cancelled.v1"
    CART_RESTORED = "cart.restored.v1"


class QueueName(StrEnum):
    ORDER_CREATED = "order.created.queue"
    PAYMENT_RESULT = "payment.result.queue"
    CART_RESTORE = "cart.restore.queue"
    DEAD_LETTER = "ecommerce.dead-letter.queue"
