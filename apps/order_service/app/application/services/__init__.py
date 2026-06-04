"""Compatibility facade for order application services."""

from apps.order_service.app.application.orders import (
    CreatedOrder,
    clear_order_state,
    create_order_for_user,
    dump_order_state,
    get_all_orders,
    get_order_status,
    save_order_status,
)
from apps.order_service.app.infrastructure.clients.cart_client import (
    get_cart_snapshot as _get_cart_snapshot,
)
from apps.order_service.app.infrastructure.clients.product_catalog_acl import (
    get_product_quote as _get_product_quote,
)
from apps.order_service.app.infrastructure.database.repository import (
    clear_orders as _clear_orders,
    get_order_record_by_id as _get_order_record_by_id,
    get_order_status_by_id as _get_order_status_by_id,
    list_order_statuses as _list_order_statuses,
    save_order_with_outbox as _save_order_with_outbox,
    update_order_status as _update_order_status,
)
from apps.order_service.app.infrastructure.messaging.outbox_publisher import (
    publish_pending_order_events as _publish_pending_order_events,
)

get_cart_snapshot = _get_cart_snapshot
get_product_quote = _get_product_quote
save_order_with_outbox = _save_order_with_outbox
publish_pending_order_events = _publish_pending_order_events
update_order_status = _update_order_status
get_order_record_by_id = _get_order_record_by_id
get_order_status_by_id = _get_order_status_by_id
list_order_statuses = _list_order_statuses
clear_orders = _clear_orders

__all__ = [
    "CreatedOrder",
    "clear_order_state",
    "clear_orders",
    "create_order_for_user",
    "dump_order_state",
    "get_cart_snapshot",
    "get_product_quote",
    "get_all_orders",
    "get_order_record_by_id",
    "get_order_status",
    "get_order_status_by_id",
    "list_order_statuses",
    "publish_pending_order_events",
    "save_order_status",
    "save_order_with_outbox",
    "update_order_status",
]
