from apps.order_service.app.infrastructure.messaging.broker import (
    broker,
    ecommerce_exchange,
)
from apps.order_service.app.infrastructure.messaging.publisher import publish_event
from apps.order_service.app.schemas.events import OrderCreatedEvent
from apps.order_service.app.schemas.topics import RoutingKey


async def publish_order_created(event: OrderCreatedEvent) -> None:
    await publish_event(
        event,
        routing_key=RoutingKey.ORDER_CREATED,
        exchange=ecommerce_exchange,
        message_broker=broker,
    )
