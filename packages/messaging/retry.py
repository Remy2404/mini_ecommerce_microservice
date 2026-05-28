"""RabbitMQ retry and dead-letter publishing helpers."""

from dataclasses import dataclass

from pydantic import BaseModel

from packages.config.settings import settings
from packages.messaging.broker import broker, dead_letter_exchange, retry_exchange
from packages.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class RetryDecision:
    should_retry: bool
    next_retry_count: int
    delay_ms: int
    routing_key: str


def calculate_retry_delay_ms(retry_count: int) -> int:
    """Return exponential backoff delay for a 1-based retry count."""
    multiplier = settings.rabbitmq_retry_backoff_multiplier ** max(retry_count - 1, 0)
    return int(settings.rabbitmq_retry_delay_ms * multiplier)


def retry_decision(
    *,
    current_retry_count: int,
    retry_routing_key: str,
    dlq_routing_key: str,
) -> RetryDecision:
    next_retry_count = current_retry_count + 1
    should_retry = next_retry_count <= settings.rabbitmq_retry_max_attempts
    return RetryDecision(
        should_retry=should_retry,
        next_retry_count=next_retry_count,
        delay_ms=calculate_retry_delay_ms(next_retry_count),
        routing_key=retry_routing_key if should_retry else dlq_routing_key,
    )


async def publish_retry_or_dlq(
    *,
    event: BaseModel,
    error: Exception,
    retry_routing_key: str,
    dlq_routing_key: str,
    service_name: str,
) -> RetryDecision:
    """Publish a failed event to retry or DLQ with bounded metadata."""
    current_retry_count = int(getattr(event, "retry_count", 0) or 0)
    decision = retry_decision(
        current_retry_count=current_retry_count,
        retry_routing_key=retry_routing_key,
        dlq_routing_key=dlq_routing_key,
    )

    message = event.model_dump(mode="json")
    message["retry_count"] = decision.next_retry_count
    message["last_error"] = str(error)[:500]

    if decision.should_retry:
        exchange = retry_exchange
        log_message = "Consumer failure routed to retry"
    else:
        exchange = dead_letter_exchange
        log_message = "Consumer failure routed to DLQ"

    await broker.publish(
        message=message,
        exchange=exchange,
        routing_key=decision.routing_key,
    )

    logger.warning(
        log_message,
        service_name=service_name,
        event_id=message.get("event_id"),
        event_type=message.get("event_type"),
        retry_count=decision.next_retry_count,
        retry_delay_ms=decision.delay_ms,
        routing_key=decision.routing_key,
        error=str(error),
    )

    return decision
