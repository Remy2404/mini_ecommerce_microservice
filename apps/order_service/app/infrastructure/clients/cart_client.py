import json
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from apps.order_service.app.domain.exceptions import CartNotFoundError, EmptyCartError
from packages.cache.valkey_client import get_valkey_client


@dataclass(frozen=True)
class CartSnapshotItem:
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


@dataclass(frozen=True)
class CartSnapshot:
    cart_id: str
    total_amount: Decimal
    items: list[CartSnapshotItem]


def get_cart_snapshot(user_id: str) -> CartSnapshot:
    client = get_valkey_client()
    raw_cart = client.get(f"cart:{user_id}")

    if raw_cart is None:
        raise CartNotFoundError("Cart not found")

    cart = json.loads(str(raw_cart))
    items = cart.get("items", [])

    if not items:
        raise EmptyCartError("Cart is empty")

    return CartSnapshot(
        cart_id=f"cart_{user_id}",
        total_amount=Decimal(str(cart["total_amount"])),
        items=[
            CartSnapshotItem(
                product_id=UUID(item["product_id"]),
                product_name=item["name"],
                quantity=int(item["quantity"]),
                unit_price=Decimal(str(item["unit_price"])),
                subtotal=Decimal(str(item["subtotal"])),
            )
            for item in items
        ],
    )


def get_cart_total_amount(user_id: str) -> Decimal:
    return get_cart_snapshot(user_id).total_amount
