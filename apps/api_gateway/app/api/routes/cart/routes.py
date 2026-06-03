from fastapi import APIRouter, Depends, Request, status

from apps.api_gateway.app.api.routes._shared import (
    enforce_gateway_access,
    enforce_user_scope,
    owner_headers,
    owned_body,
)
from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request
from apps.api_gateway.app.schemas.requests import (
    GatewayAddCartItemRequest,
    swagger_request_body,
)

router = APIRouter(prefix="/cart", tags=["Cart Gateway"])


@router.get("/{user_id}")
async def get_cart(
    user_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    enforce_user_scope(payload, user_id)
    return await forward_request(
        "cart",
        user_id,
        request,
        extra_headers=owner_headers(payload),
    )


@router.post(
    "/items",
    status_code=status.HTTP_201_CREATED,
    openapi_extra=swagger_request_body(GatewayAddCartItemRequest),
)
async def add_cart_item(
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "cart",
        "items",
        request,
        body_override=await owned_body(request),
        extra_headers=owner_headers(payload),
    )


@router.delete("/{user_id}/items/{product_id}")
async def remove_cart_item(
    user_id: str,
    product_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    enforce_user_scope(payload, user_id)
    return await forward_request(
        "cart",
        f"{user_id}/items/{product_id}",
        request,
        extra_headers=owner_headers(payload),
    )


@router.delete("/{user_id}")
async def clear_cart(
    user_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    enforce_user_scope(payload, user_id)
    return await forward_request(
        "cart",
        user_id,
        request,
        extra_headers=owner_headers(payload),
    )
