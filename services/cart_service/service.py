from decimal import Decimal
from http import HTTPStatus
from uuid import UUID

import httpx
from pydantic import ValidationError

from packages.config.settings import settings
from packages.contracts.schemas import ApiResponse, ProductResponse
from services.cart_service.repository import (
    clear_cart,
    get_cart,
    remove_cart_item,
    save_cart,
)
from services.cart_service.schemas import (
    AddCartItemRequest,
    CartItemResponse,
    CartResponse,
)


class ProductNotFoundError(Exception):
    """Raised when the requested product does not exist."""


class ProductLookupRejectedError(Exception):
    """Raised when Product Service rejects a product lookup."""


class ProductServiceUnavailableError(Exception):
    """Raised when trusted product data cannot be fetched safely."""


def _product_url(product_id: UUID) -> str:
    return f"{settings.product_service_url.rstrip('/')}/products/{product_id}"


async def fetch_product(product_id: UUID) -> ProductResponse:
    try:
        async with httpx.AsyncClient(
            timeout=settings.gateway_request_timeout_seconds,
        ) as client:
            response = await client.get(_product_url(product_id))
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
        raise ProductServiceUnavailableError from exc
    except httpx.HTTPError as exc:
        raise ProductServiceUnavailableError from exc

    if response.status_code == HTTPStatus.NOT_FOUND:
        raise ProductNotFoundError

    if response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        raise ProductServiceUnavailableError

    if response.status_code >= HTTPStatus.BAD_REQUEST:
        raise ProductLookupRejectedError

    try:
        product_response = ApiResponse[ProductResponse].model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise ProductServiceUnavailableError from exc

    product = product_response.data
    if (
        not product_response.success
        or product is None
        or product.product_id != product_id
    ):
        raise ProductServiceUnavailableError

    return product


async def add_item_to_cart(request: AddCartItemRequest) -> CartResponse:
    product = await fetch_product(request.product_id)
    cart = get_cart(request.user_id)

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
        user_id=request.user_id,
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
