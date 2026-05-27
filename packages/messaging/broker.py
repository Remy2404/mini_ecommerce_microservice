from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from faststream.rabbit.schemas.constants import ExchangeType
from packages.config.settings import settings
from packages.contracts.order.topics import ExchangeName, QueueName, RoutingKey

broker = RabbitBroker(settings.rabbitmq_url)

ecommerce_exchange = RabbitExchange(
    name=ExchangeName.ECOMMERCE,
    type=ExchangeType.TOPIC,
    durable=True,
)

retry_exchange = RabbitExchange(
    name=ExchangeName.RETRY,
    type=ExchangeType.TOPIC,
    durable=True,
)

dead_letter_exchange = RabbitExchange(
    name=ExchangeName.DEAD_LETTER,
    type=ExchangeType.TOPIC,
    durable=True,
)

order_created_queue = RabbitQueue(
    name=QueueName.ORDER_CREATED,
    routing_key=RoutingKey.ORDER_CREATED,
    durable=True,
    arguments={
        "x-dead-letter-exchange": ExchangeName.DEAD_LETTER,
        "x-dead-letter-routing-key": RoutingKey.ORDER_CREATED_DLQ,
    },
)

payment_result_queue = RabbitQueue(
    name=QueueName.PAYMENT_RESULT,
    routing_key="payment.*.v1",
    durable=True,
    arguments={
        "x-dead-letter-exchange": ExchangeName.DEAD_LETTER,
        "x-dead-letter-routing-key": RoutingKey.PAYMENT_FAILED_DLQ,
    },
)

cart_restore_queue = RabbitQueue(
    name=QueueName.CART_RESTORE,
    routing_key=RoutingKey.CART_RESTORED,
    durable=True,
)

order_created_retry_queue = RabbitQueue(
    name=QueueName.ORDER_CREATED_RETRY,
    routing_key=RoutingKey.ORDER_CREATED_RETRY,
    durable=True,
    arguments={
        "x-message-ttl": settings.rabbitmq_retry_delay_ms,
        "x-dead-letter-exchange": ExchangeName.ECOMMERCE,
        "x-dead-letter-routing-key": RoutingKey.ORDER_CREATED,
    },
)

payment_success_retry_queue = RabbitQueue(
    name=QueueName.PAYMENT_SUCCESS_RETRY,
    routing_key=RoutingKey.PAYMENT_SUCCESS_RETRY,
    durable=True,
    arguments={
        "x-message-ttl": settings.rabbitmq_retry_delay_ms,
        "x-dead-letter-exchange": ExchangeName.ECOMMERCE,
        "x-dead-letter-routing-key": RoutingKey.PAYMENT_SUCCESS,
    },
)

payment_failed_retry_queue = RabbitQueue(
    name=QueueName.PAYMENT_FAILED_RETRY,
    routing_key=RoutingKey.PAYMENT_FAILED_RETRY,
    durable=True,
    arguments={
        "x-message-ttl": settings.rabbitmq_retry_delay_ms,
        "x-dead-letter-exchange": ExchangeName.ECOMMERCE,
        "x-dead-letter-routing-key": RoutingKey.PAYMENT_FAILED,
    },
)

dead_letter_queue = RabbitQueue(
    name=QueueName.DEAD_LETTER,
    routing_key="#",
    durable=True,
)
