import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("api_gateway")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        # Log incoming request
        logger.info(
            f"→ {request.method} {request.url.path} "
            f"client={request.client.host if request.client else 'unknown'}"
        )

        response = await call_next(request)

        duration = (time.perf_counter() - start) * 1000  # ms
        logger.info(
            f"← {request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration:.2f}ms"
        )

        return response