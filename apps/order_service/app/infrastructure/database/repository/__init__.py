"""Order Service repository facade."""

from apps.order_service.app.infrastructure.database.repository.orders import (
    apply_payment_result_once,
    save_order,
    save_order_with_outbox,
    update_order_status,
)
from apps.order_service.app.infrastructure.database.repository.outbox import (
    claim_pending_outbox_events,
    mark_outbox_event_failed,
    mark_outbox_event_published,
)
from apps.order_service.app.infrastructure.database.repository.queries import (
    clear_orders,
    get_order_record_by_id,
    get_order_status_by_id,
    list_order_statuses,
)
from apps.order_service.app.infrastructure.database.repository.types import (
    OrderRecord,
    PendingOutboxEvent,
)

__all__ = [
    "OrderRecord",
    "PendingOutboxEvent",
    "apply_payment_result_once",
    "clear_orders",
    "claim_pending_outbox_events",
    "get_order_record_by_id",
    "get_order_status_by_id",
    "list_order_statuses",
    "mark_outbox_event_failed",
    "mark_outbox_event_published",
    "save_order",
    "save_order_with_outbox",
    "update_order_status",
]
