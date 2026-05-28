"""Consumer registration helpers used by service workers."""

from collections.abc import Callable, Coroutine
from typing import Any

from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from pydantic import BaseModel

from packages.messaging.serialization import parse_event


def subscribe_event(
    broker: RabbitBroker,
    *,
    queue: RabbitQueue,
    exchange: RabbitExchange,
    event_model: type[BaseModel],
):
    def decorator(handler: Callable[[Any], Coroutine[Any, Any, None]]):
        @broker.subscriber(queue=queue, exchange=exchange)
        async def wrapped(message: dict[str, Any] | BaseModel) -> None:
            await handler(parse_event(event_model, message))

        return wrapped

    return decorator
