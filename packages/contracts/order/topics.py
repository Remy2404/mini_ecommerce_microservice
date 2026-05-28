from enum import StrEnum


class ExchangeName(StrEnum):
    ECOMMERCE = "ecommerce.exchange"
    RETRY = "ecommerce.retry.exchange"
    DEAD_LETTER = "ecommerce.dlx"


class RoutingKey(StrEnum):
    ORDER_CREATED = "order.created.v1"
    PAYMENT_SUCCESS = "payment.succeeded.v1"
    PAYMENT_FAILED = "payment.failed.v1"
    ORDER_CONFIRMED = "order.confirmed.v1"
    ORDER_CANCELLED = "order.cancelled.v1"
    CART_RESTORED = "cart.restored.v1"
    ORDER_CREATED_RETRY = "order.created.retry.v1"
    PAYMENT_SUCCESS_RETRY = "payment.succeeded.retry.v1"
    PAYMENT_FAILED_RETRY = "payment.failed.retry.v1"
    ORDER_CREATED_DLQ = "dead.order.created.v1"
    PAYMENT_SUCCESS_DLQ = "dead.payment.succeeded.v1"
    PAYMENT_FAILED_DLQ = "dead.payment.failed.v1"


class QueueName(StrEnum):
    ORDER_CREATED = "order.created.queue"
    PAYMENT_RESULT = "payment.result.queue"
    CART_RESTORE = "cart.restore.queue"
    ORDER_CREATED_RETRY = "order.created.retry.queue"
    PAYMENT_SUCCESS_RETRY = "payment.succeeded.retry.queue"
    PAYMENT_FAILED_RETRY = "payment.failed.retry.queue"
    DEAD_LETTER = "ecommerce.dead-letter.queue"
