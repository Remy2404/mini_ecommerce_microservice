"""Serialization helpers for RabbitMQ event payloads."""

from typing import Any, TypeVar

from pydantic import BaseModel

EventModel = TypeVar("EventModel", bound=BaseModel)


def event_to_message(event: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(event, BaseModel):
        return event.model_dump(mode="json")

    return event


def parse_event(model: type[EventModel], message: dict[str, Any] | BaseModel) -> EventModel:
    if isinstance(message, model):
        return message

    if isinstance(message, BaseModel):
        return model.model_validate(message.model_dump(mode="json"))

    return model.model_validate(message)
