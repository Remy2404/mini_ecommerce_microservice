from fastapi import APIRouter, Depends, Request, status

from apps.api_gateway.app.api.routes._shared import enforce_gateway_access
from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request
from apps.api_gateway.app.schemas.requests import (
    GatewayCreateProductRequest,
    swagger_multipart_file_request_body,
    swagger_request_body,
)
from apps.api_gateway.app.schemas.responses import DetailErrorResponse

router = APIRouter(prefix="/products", tags=["Product Gateway"])


@router.get("")
async def list_products(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", "", request)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    openapi_extra=swagger_request_body(GatewayCreateProductRequest),
)
async def create_product(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", "", request)


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", product_id, request)


@router.put(
    "/{product_id}/image",
    summary="Upload a product image",
    description=(
        "Uploads a product image through the gateway. The request must be sent "
        "as multipart/form-data with a single file field named `file`. "
        "Requires a bearer token that includes the `product_image_write` scope."
    ),
    responses={
        401: {"model": DetailErrorResponse, "description": "Missing or invalid token."},
        403: {
            "model": DetailErrorResponse,
            "description": "Missing required scope `product_image_write`.",
        },
        503: {"model": DetailErrorResponse, "description": "Downstream service unavailable."},
    },
    openapi_extra=swagger_multipart_file_request_body(
        file_field_name="file",
        file_description="Product image file.",
    ),
)
async def upload_product_image(
    product_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", f"{product_id}/image", request)
