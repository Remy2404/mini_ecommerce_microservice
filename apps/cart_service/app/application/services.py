from decimal import Decimal
from uuid import UUID

from apps.cart_service.app.domain.exceptions import (
    ProductLookupRejectedError,
    ProductNotFoundError,
    ProductServiceUnavailableError,
)
from apps.cart_service.app.infrastructure.clients.product_client import fetch_product
from apps.cart_service.app.infrastructure.cache.cart_repository import (
    clear_cart,
    get_cart,
    remove_cart_item,
    save_cart,
)
from apps.cart_service.app.schemas import (
    AddCartItemRequest,
    CartItemResponse,
    CartResponse,
)

__all__ = [
    "ProductLookupRejectedError",
    "ProductNotFoundError",
    "ProductServiceUnavailableError",
    "add_item_to_cart",
    "delete_cart",
    "delete_cart_item",
    "find_cart",
]


async def add_item_to_cart(user_id: str, request: AddCartItemRequest) -> CartResponse:
    product = await fetch_product(request.product_id)
    cart = get_cart(user_id)

    items = list(cart.items)
    existing_item_index = next(
        (
            index
            for index, item in enumerate(items)
            if item.product_id == request.product_id
        ),
        None,
    )

    if existing_item_index is not None:
        existing_item = items[existing_item_index]
        new_quantity = existing_item.quantity + request.quantity

        items[existing_item_index] = CartItemResponse(
            product_id=existing_item.product_id,
            name=product.name,
            quantity=new_quantity,
            unit_price=product.price,
            subtotal=product.price * new_quantity,
        )
    else:
        items.append(
            CartItemResponse(
                product_id=request.product_id,
                name=product.name,
                quantity=request.quantity,
                unit_price=product.price,
                subtotal=product.price * request.quantity,
            )
        )

    total_amount = sum(
        (item.subtotal for item in items),
        Decimal("0"),
    )

    updated_cart = CartResponse(
        user_id=user_id,
        items=items,
        total_amount=total_amount,
    )

    save_cart(updated_cart)

    return updated_cart


def find_cart(user_id: str) -> CartResponse:
    return get_cart(user_id)


def delete_cart_item(user_id: str, product_id: UUID) -> CartResponse:
    return remove_cart_item(
        user_id=user_id,
        product_id=product_id,
    )


def delete_cart(user_id: str) -> None:
    clear_cart(user_id)
