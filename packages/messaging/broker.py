from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

from packages.config.settings import settings
from packages.contracts.topics import ExchangeName, QueueName, RoutingKey

broker = RabbitBroker(settings.rabbitmq_url)

ecommerce_exchange = RabbitExchange(
    name=ExchangeName.ECOMMERCE,
    type="topic",
    durable=True,
)

order_created_queue = RabbitQueue(
    name=QueueName.ORDER_CREATED,
    routing_key=RoutingKey.ORDER_CREATED,
    durable=True,
)

payment_result_queue = RabbitQueue(
    name=QueueName.PAYMENT_RESULT,
    routing_key="payment.*",
    durable=True,
)

cart_restore_queue = RabbitQueue(
    name=QueueName.CART_RESTORE,
    routing_key=RoutingKey.CART_RESTORED,
    durable=True,
)
