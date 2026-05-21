import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.dependencies.auth import validate_token
from app.dependencies.rate_limit import rate_limit
from app.config import settings

router = APIRouter()

SERVICE_MAP = {
    "users":    settings.USER_SERVICE_URL,
    "orders":   settings.ORDER_SERVICE_URL,
    "products": settings.PRODUCT_SERVICE_URL,
}

async def _proxy(request: Request, base_url: str, service: str) -> Response:
    """Forward the request to a downstream service, preserving method/body/headers."""
    full_path = request.url.path                        # /api/v1/products  or  /api/v1/products/123
    stripped  = full_path.split(f"/{service}", 1)[-1]  # ""                or  "/123"
    url       = f"{base_url}/{service}{stripped}"       # http://localhost:8003/products

    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient() as client:
        upstream = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=await request.body(),
            params=request.query_params,
            timeout=10.0,
        )

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(upstream.headers),
        media_type=upstream.headers.get("content-type"),
    )

@router.api_route(
    "/{service}{path:path}",    # ← removed the slash between {service} and {path:path}
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def gateway(
    service: str,
    path: str,
    request: Request,
    payload: dict = Depends(validate_token),
):
    await rate_limit(request, payload)

    base = SERVICE_MAP.get(service)
    if not base:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service}")

    return await _proxy(request, base, service)