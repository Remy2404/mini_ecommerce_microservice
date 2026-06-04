"""External service clients used by order workflows."""

from apps.order_service.app.infrastructure.clients.cart_client import (
    CartSnapshot,
    CartSnapshotItem,
    get_cart_snapshot,
    get_cart_total_amount,
)
from apps.order_service.app.infrastructure.clients.product_catalog_acl import (
    ProductCatalogQuote,
    ProductQuoteLine,
    get_product_quote,
)

__all__ = [
    "CartSnapshot",
    "CartSnapshotItem",
    "ProductCatalogQuote",
    "ProductQuoteLine",
    "get_cart_snapshot",
    "get_cart_total_amount",
    "get_product_quote",
]

