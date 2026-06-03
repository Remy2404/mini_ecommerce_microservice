from typing import Any

from faststream.rabbit import RabbitBroker, RabbitExchange
from pydantic import BaseModel

from apps.order_service.app.infrastructure.messaging.broker import (
    broker,
    ecommerce_exchange,
)
from apps.order_service.app.infrastructure.messaging.serialization import (
    event_to_message,
)


async def publish_event(
    event: BaseModel | dict[str, Any],
    *,
    routing_key: str,
    exchange: RabbitExchange = ecommerce_exchange,
    message_broker: RabbitBroker = broker,
) -> None:
    await message_broker.publish(
        message=event_to_message(event),
        exchange=exchange,
        routing_key=routing_key,
    )
