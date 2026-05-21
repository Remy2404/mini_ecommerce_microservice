import json
from decimal import Decimal
from uuid import UUID

from packages.cache.valkey_client import get_valkey_client
from services.cart_service.schemas import CartItemResponse, CartResponse

CART_KEY_PREFIX = "cart"


def _cart_key(user_id: str) -> str:
    return f"{CART_KEY_PREFIX}:{user_id}"


def save_cart(cart: CartResponse) -> None:
    client = get_valkey_client()

    payload = cart.model_dump(mode="json")
    payload["total_amount"] = str(cart.total_amount)

    for item in payload["items"]:
        item["unit_price"] = str(item["unit_price"])
        item["subtotal"] = str(item["subtotal"])

    client.set(
        _cart_key(cart.user_id),
        json.dumps(payload),
    )


def get_cart(user_id: str) -> CartResponse:
    client = get_valkey_client()

    raw_cart = client.get(_cart_key(user_id))

    if raw_cart is None:
        return CartResponse(
            user_id=user_id,
            items=[],
            total_amount=Decimal("0"),
        )

    data = json.loads(str(raw_cart))

    data["total_amount"] = Decimal(data["total_amount"])

    for item in data["items"]:
        item["unit_price"] = Decimal(item["unit_price"])
        item["subtotal"] = Decimal(item["subtotal"])
        item["product_id"] = UUID(item["product_id"])

    return CartResponse(**data)


def clear_cart(user_id: str) -> None:
    client = get_valkey_client()

    client.delete(_cart_key(user_id))


def remove_cart_item(user_id: str, product_id: UUID) -> CartResponse:
    cart = get_cart(user_id)

    remaining_items = [item for item in cart.items if item.product_id != product_id]

    total_amount = sum(
        (item.subtotal for item in remaining_items),
        Decimal("0"),
    )

    updated_cart = CartResponse(
        user_id=user_id,
        items=remaining_items,
        total_amount=total_amount,
    )

    save_cart(updated_cart)

    return updated_cart
