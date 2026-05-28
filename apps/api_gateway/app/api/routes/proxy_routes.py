from fastapi import APIRouter, Depends, Request

from apps.api_gateway.app.api.dependencies import rate_limit, validate_token
from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request

router = APIRouter()


@router.api_route(
    "/{service}{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def gateway(
    service: str,
    path: str,
    request: Request,
    payload: dict = Depends(validate_token),
):
    await rate_limit(request, payload)

    return await forward_request(service, path, request)
