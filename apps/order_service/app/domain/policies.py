"""Order Service policy checks."""

from decimal import Decimal

from apps.order_service.app.domain.exceptions import EmptyCartError


def ensure_cart_can_be_ordered(*, total_amount: Decimal, items_count: int) -> None:
    if items_count <= 0 or total_amount <= 0:
        raise EmptyCartError("Cart is empty")
