from packages.contracts.topics import ExchangeName, QueueName
from packages.messaging.broker import (
    broker,
    cart_restore_queue,
    dead_letter_exchange,
    dead_letter_queue,
    ecommerce_exchange,
    order_created_queue,
    order_created_retry_queue,
    payment_result_queue,
    payment_failed_retry_queue,
    payment_success_retry_queue,
    retry_exchange,
)


def test_broker_is_configured():
    assert broker is not None


def test_exchange_name_is_correct():
    assert ecommerce_exchange.name == ExchangeName.ECOMMERCE
    assert retry_exchange.name == ExchangeName.RETRY
    assert dead_letter_exchange.name == ExchangeName.DEAD_LETTER


def test_queue_names_are_correct():
    assert order_created_queue.name == QueueName.ORDER_CREATED
    assert payment_result_queue.name == QueueName.PAYMENT_RESULT
    assert cart_restore_queue.name == QueueName.CART_RESTORE
    assert order_created_retry_queue.name == QueueName.ORDER_CREATED_RETRY
    assert payment_success_retry_queue.name == QueueName.PAYMENT_SUCCESS_RETRY
    assert payment_failed_retry_queue.name == QueueName.PAYMENT_FAILED_RETRY
    assert dead_letter_queue.name == QueueName.DEAD_LETTER
