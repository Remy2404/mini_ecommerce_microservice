import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from packages.observability.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()
        status_code = 500

        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id

        duration = (time.perf_counter() - start) * 1000  # ms
        logger.info(
            "Gateway request completed",
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=round(duration, 2),
            request_id=request_id,
        )

        return response
