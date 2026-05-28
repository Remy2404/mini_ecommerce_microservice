"""Payment messaging bindings used by payment service workers.

This module keeps payment-specific worker imports small while sharing the
central RabbitMQ broker, ecommerce exchange, and queue definitions.
"""

from packages.messaging.broker import (
    broker,
    ecommerce_exchange,
    order_created_queue,
    payment_result_queue,
)

__all__ = [
    "broker",
    "ecommerce_exchange",
    "order_created_queue",
    "payment_result_queue",
]
