from ecommerce_contracts.order.events import OrderCreatedEvent
from ecommerce_contracts.order.topics import RoutingKey
from ecommerce_messaging.broker import broker, ecommerce_exchange
from ecommerce_messaging.publisher import publish_event


async def publish_order_created(event: OrderCreatedEvent) -> None:
    await publish_event(
        event,
        routing_key=RoutingKey.ORDER_CREATED,
        exchange=ecommerce_exchange,
        message_broker=broker,
    )

