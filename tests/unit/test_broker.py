from packages.contracts.topics import ExchangeName, QueueName
from packages.messaging.broker import (
    broker,
    cart_restore_queue,
    ecommerce_exchange,
    order_created_queue,
    payment_result_queue,
)


def test_broker_is_configured():
    assert broker is not None


def test_exchange_name_is_correct():
    assert ecommerce_exchange.name == ExchangeName.ECOMMERCE


def test_queue_names_are_correct():
    assert order_created_queue.name == QueueName.ORDER_CREATED
    assert payment_result_queue.name == QueueName.PAYMENT_RESULT
    assert cart_restore_queue.name == QueueName.CART_RESTORE
