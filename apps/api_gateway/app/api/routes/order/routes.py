from fastapi import APIRouter, Depends, Request, status

from apps.api_gateway.app.api.routes._shared import (
    enforce_gateway_access,
    owner_headers,
    owned_body,
)
from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request
from apps.api_gateway.app.schemas.requests import (
    GatewayCreateOrderRequest,
    swagger_request_body,
)

router = APIRouter(prefix="/orders", tags=["Order Gateway"])


@router.get("")
async def list_orders(
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "orders",
        "",
        request,
        extra_headers=owner_headers(payload),
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    openapi_extra=swagger_request_body(GatewayCreateOrderRequest),
    description=(
        "Create an order for the authenticated user. "
        "Send an empty JSON object; the gateway injects the user identity from headers."
    ),
)
async def create_order(
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "orders",
        "",
        request,
        body_override=await owned_body(request),
        extra_headers=owner_headers(payload),
    )


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "orders",
        order_id,
        request,
        extra_headers=owner_headers(payload),
    )
