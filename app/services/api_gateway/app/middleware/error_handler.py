from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from packages.observability.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(
                "Unhandled gateway error",
                method=request.method,
                path=request.url.path,
                request_id=getattr(request.state, "request_id", None),
                error_type=type(exc).__name__,
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal gateway error"},
            )
