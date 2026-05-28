"""Payment Service outbox publisher worker."""

import asyncio

from packages.config.settings import settings
from packages.observability.logging import get_logger, setup_logging
from packages.observability.tracing import setup_tracing

from apps.payment_service.app.infrastructure.messaging.outbox_publisher import (
    publish_pending_payment_events,
)

setup_logging(settings.payment_service_name)
setup_tracing(settings.payment_service_name)

logger = get_logger(__name__)


async def main(poll_interval_seconds: float = 2.0) -> None:
    logger.info("Starting payment outbox publisher worker")
    while True:
        await publish_pending_payment_events()
        await asyncio.sleep(poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
