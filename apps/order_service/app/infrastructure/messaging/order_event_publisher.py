from packages.contracts.order.events import OrderCreatedEvent
from packages.contracts.order.topics import RoutingKey
from packages.messaging.broker import broker, ecommerce_exchange


async def publish_order_created(event: OrderCreatedEvent) -> None:
    await broker.publish(
        message=event.model_dump(mode="json"),
        exchange=ecommerce_exchange,
        routing_key=RoutingKey.ORDER_CREATED,
    )
