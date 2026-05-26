from enum import StrEnum


class ExchangeName(StrEnum):
    ECOMMERCE = "ecommerce.exchange"


class RoutingKey(StrEnum):
    ORDER_CREATED = "order.created"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_CANCELLED = "order.cancelled"
    CART_RESTORED = "cart.restored"


class QueueName(StrEnum):
    ORDER_CREATED = "order.created.queue"
    PAYMENT_RESULT = "payment.result.queue"
    CART_RESTORE = "cart.restore.queue"
    DEAD_LETTER = "ecommerce.dead-letter.queue"
