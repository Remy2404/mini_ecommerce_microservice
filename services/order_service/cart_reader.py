import json
from decimal import Decimal

from packages.cache.valkey_client import get_valkey_client


class CartNotFoundError(Exception):
    pass


class EmptyCartError(Exception):
    pass


def get_cart_total_amount(user_id: str) -> Decimal:
    client = get_valkey_client()
    raw_cart = client.get(f"cart:{user_id}")

    if raw_cart is None:
        raise CartNotFoundError("Cart not found")

    cart = json.loads(str(raw_cart))
    items = cart.get("items", [])

    if not items:
        raise EmptyCartError("Cart is empty")

    return Decimal(str(cart["total_amount"]))
