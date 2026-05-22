from fastapi import APIRouter, Depends, Request

from services.api_gateway.app.dependencies.auth import validate_token
from services.api_gateway.app.dependencies.rate_limit import rate_limit
from services.api_gateway.app.routers.proxy import forward_request

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
