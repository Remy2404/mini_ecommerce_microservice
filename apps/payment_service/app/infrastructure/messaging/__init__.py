"""Payment Service messaging consumers."""

from apps.payment_service.app.infrastructure.messaging.order_created_consumer import (
    main,
    process_payment,
)

__all__ = ["main", "process_payment"]
