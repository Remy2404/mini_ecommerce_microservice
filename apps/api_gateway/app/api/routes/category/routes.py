from fastapi import APIRouter, Depends, Request, status

from apps.api_gateway.app.api.routes._shared import enforce_gateway_access
from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request
from apps.api_gateway.app.schemas.requests import (
    GatewayCreateCategoryRequest,
    swagger_request_body,
)

router = APIRouter(prefix="/categories", tags=["Category Gateway"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    openapi_extra=swagger_request_body(GatewayCreateCategoryRequest),
)
async def create_category(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("categories", "", request)


@router.get("")
async def list_categories(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("categories", "", request)
