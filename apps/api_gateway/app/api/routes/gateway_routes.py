from fastapi import APIRouter, Depends, Request

from apps.api_gateway.app.api.dependencies import rate_limit, validate_token
from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request

router = APIRouter()

JSON_REQUEST_BODY = {
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {"type": "object"},
            },
        },
        "required": False,
    },
}


async def enforce_gateway_access(
    request: Request,
    payload: dict = Depends(validate_token),
) -> dict:
    await rate_limit(request, payload)
    return payload


@router.get("/products", tags=["Product Gateway"])
async def list_products(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", "", request)


@router.post(
    "/auth/register",
    tags=["Auth Gateway"],
    openapi_extra=JSON_REQUEST_BODY,
)
async def register_user(
    request: Request,
):
    return await forward_request("auth", "register", request)


@router.post(
    "/auth/login",
    tags=["Auth Gateway"],
    openapi_extra=JSON_REQUEST_BODY,
)
async def login_user(
    request: Request,
):
    return await forward_request("auth", "login", request)


@router.get("/auth/me", tags=["Auth Gateway"])
async def get_me(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", "me", request)


@router.post(
    "/auth/addresses",
    tags=["Auth Gateway"],
    openapi_extra=JSON_REQUEST_BODY,
)
async def create_address(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", "addresses", request)


@router.get("/auth/addresses", tags=["Auth Gateway"])
async def list_addresses(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", "addresses", request)


@router.post(
    "/categories",
    tags=["Category Gateway"],
    openapi_extra=JSON_REQUEST_BODY,
)
async def create_category(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("categories", "", request)


@router.get("/categories", tags=["Category Gateway"])
async def list_categories(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("categories", "", request)


@router.post(
    "/products",
    tags=["Product Gateway"],
    openapi_extra=JSON_REQUEST_BODY,
)
async def create_product(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", "", request)


@router.get("/products/{product_id}", tags=["Product Gateway"])
async def get_product(
    product_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", product_id, request)


@router.get("/cart/{user_id}", tags=["Cart Gateway"])
async def get_cart(
    user_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("cart", user_id, request)


@router.post(
    "/cart/items",
    tags=["Cart Gateway"],
    openapi_extra=JSON_REQUEST_BODY,
)
async def add_cart_item(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("cart", "items", request)


@router.delete("/cart/{user_id}/items/{product_id}", tags=["Cart Gateway"])
async def remove_cart_item(
    user_id: str,
    product_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("cart", f"{user_id}/items/{product_id}", request)


@router.delete("/cart/{user_id}", tags=["Cart Gateway"])
async def clear_cart(
    user_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("cart", user_id, request)


@router.get("/orders", tags=["Order Gateway"])
async def list_orders(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("orders", "", request)


@router.post(
    "/orders",
    tags=["Order Gateway"],
    openapi_extra=JSON_REQUEST_BODY,
)
async def create_order(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("orders", "", request)


@router.get("/orders/{order_id}", tags=["Order Gateway"])
async def get_order(
    order_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("orders", order_id, request)


@router.get("/payments/{payment_id}", tags=["Payment Gateway"])
async def get_payment(
    payment_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("payments", payment_id, request)
