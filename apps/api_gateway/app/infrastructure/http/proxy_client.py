import httpx
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from packages.config.settings import settings

SERVICE_MAP = {
    "auth": "auth_service_url",
    "categories": "product_service_url",
    "products": "product_service_url",
    "cart": "cart_service_url",
    "orders": "order_service_url",
    "payments": "payment_service_url",
}

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}

REQUEST_HEADERS_TO_DROP = HOP_BY_HOP_HEADERS | {
    "host",
    "content-length",
    "x-request-id",
}

RESPONSE_HEADERS_TO_DROP = HOP_BY_HOP_HEADERS | {
    "content-length",
}

SAFE_DOWNSTREAM_ERROR_DETAILS = {
    "Authentication service unavailable",
    "WSO2 registration configuration error",
}


def _get_base_url(service: str) -> str | None:
    setting_name = SERVICE_MAP.get(service)
    if setting_name is None:
        return None

    return getattr(settings, setting_name)


def _build_downstream_url(base_url: str, service: str, path: str) -> str:
    suffix = path if path.startswith("/") else f"/{path}" if path else ""
    return f"{base_url.rstrip('/')}/{service}{suffix}"


def _forward_request_headers(request: Request) -> dict[str, str]:
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in REQUEST_HEADERS_TO_DROP
    }

    request_id = getattr(request.state, "request_id", None)
    if request_id:
        headers["X-Request-ID"] = request_id

    return headers


def _forward_response_headers(upstream: httpx.Response) -> dict[str, str]:
    return {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in RESPONSE_HEADERS_TO_DROP
    }


def _safe_downstream_error(upstream: httpx.Response) -> dict[str, str] | None:
    try:
        body = upstream.json()
    except ValueError:
        return None

    if not isinstance(body, dict):
        return None

    detail = body.get("detail")
    if isinstance(detail, str) and detail in SAFE_DOWNSTREAM_ERROR_DETAILS:
        return {"detail": detail}

    return None


async def forward_request(
    service_name: str,
    path: str,
    request: Request,
    *,
    body_override: bytes | None = None,
    extra_headers: dict[str, str] | None = None,
) -> Response:
    """Forward a gateway request to the configured downstream service."""
    base_url = _get_base_url(service_name)
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown service",
        )

    url = _build_downstream_url(base_url, service_name, path)

    headers = _forward_request_headers(request)
    if extra_headers:
        headers.update(extra_headers)

    try:
        async with httpx.AsyncClient(
            timeout=settings.gateway_request_timeout_seconds,
        ) as client:
            upstream = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body_override if body_override is not None else await request.body(),
                params=request.query_params,
            )
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Downstream service unavailable"},
        )
    except httpx.HTTPError:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": "Downstream service error"},
        )

    if upstream.status_code >= 500:
        safe_error = _safe_downstream_error(upstream)
        if safe_error is not None:
            return JSONResponse(
                status_code=upstream.status_code,
                content=safe_error,
            )

        return JSONResponse(
            status_code=upstream.status_code,
            content={"detail": "Downstream service error"},
        )

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=_forward_response_headers(upstream),
        media_type=upstream.headers.get("content-type"),
    )
