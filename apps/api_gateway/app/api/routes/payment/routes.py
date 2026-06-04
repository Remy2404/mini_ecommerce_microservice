from fastapi import APIRouter, Depends, Request

from apps.api_gateway.app.api.routes._shared import (
    enforce_gateway_access,
    owner_headers,
)
from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request

router = APIRouter(prefix="/payments", tags=["Payment Gateway"])


@router.get("/{payment_id}")
async def get_payment(
    payment_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "payments",
        payment_id,
        request,
        extra_headers=owner_headers(payload),
    )


@router.get("/by-order/{order_id}")
async def get_payment_by_order(
    order_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "payments",
        f"by-order/{order_id}",
        request,
        extra_headers=owner_headers(payload),
    )
