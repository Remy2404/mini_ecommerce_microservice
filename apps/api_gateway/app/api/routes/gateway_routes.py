from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from apps.api_gateway.app.api.dependencies import rate_limit, validate_token
from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request
from apps.api_gateway.app.schemas.requests import WSO2PasswordLoginRequest
from packages.config.settings import settings
from packages.errors.exceptions import ForbiddenError
from packages.security.permissions import require_owner_or_role
from packages.security.wso2_login import request_wso2_password_token

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


def enforce_user_scope(payload: dict, resource_user_id: str) -> None:
    if not settings.gateway_auth_enabled:
        return

    try:
        require_owner_or_role(
            resource_owner_id=resource_user_id,
            current_user_id=str(payload.get("sub", "")),
            user_roles=payload.get("roles", []),
            role="admin",
        )
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        ) from exc


async def enforce_body_user_scope(request: Request, payload: dict) -> None:
    if not settings.gateway_auth_enabled:
        return

    body = await request.json()
    user_id = body.get("user_id") if isinstance(body, dict) else None
    if not user_id:
        raise HTTPException(
            status_code=422,
            detail="user_id is required",
        )

    enforce_user_scope(payload, str(user_id))


@router.get("/products", tags=["Product Gateway"])
async def list_products(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", "", request)


@router.post(
    "/auth/register",
    tags=["WSO2 Gateway"],
    openapi_extra=JSON_REQUEST_BODY,
)
async def register_user(
    request: Request,
):
    return await forward_request("auth", "register", request)


@router.post(
    "/auth/login",
    tags=["WSO2 Gateway"],
    summary="Login via WSO2 Identity Server",
    description=(
        "Authenticates against WSO2 and returns the WSO2 token response. Copy "
        "the full WSO2 invitation password exactly, including trailing symbols."
    ),
)
async def login_user(request: WSO2PasswordLoginRequest) -> dict[str, Any]:
    return await request_wso2_password_token(
        username=request.username,
        password=request.password.get_secret_value(),
        scope=request.scope,
    )


@router.get("/auth/me", tags=["WSO2 Gateway"])
async def get_me(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", "me", request)


@router.post(
    "/auth/addresses",
    tags=["WSO2 Gateway"],
    openapi_extra=JSON_REQUEST_BODY,
)
async def create_address(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", "addresses", request)


@router.get("/auth/addresses", tags=["WSO2 Gateway"])
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
    payload: dict = Depends(enforce_gateway_access),
):
    enforce_user_scope(payload, user_id)
    return await forward_request("cart", user_id, request)


@router.post(
    "/cart/items",
    tags=["Cart Gateway"],
    openapi_extra=JSON_REQUEST_BODY,
)
async def add_cart_item(
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    await enforce_body_user_scope(request, payload)
    return await forward_request("cart", "items", request)


@router.delete("/cart/{user_id}/items/{product_id}", tags=["Cart Gateway"])
async def remove_cart_item(
    user_id: str,
    product_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    enforce_user_scope(payload, user_id)
    return await forward_request("cart", f"{user_id}/items/{product_id}", request)


@router.delete("/cart/{user_id}", tags=["Cart Gateway"])
async def clear_cart(
    user_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    enforce_user_scope(payload, user_id)
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
    payload: dict = Depends(enforce_gateway_access),
):
    await enforce_body_user_scope(request, payload)
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
