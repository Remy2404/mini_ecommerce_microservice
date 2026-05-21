import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from packages.observability.metrics import http_request_total, http_request_duration_seconds

class HTTPMetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        # Do not record metrics for the metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start_time
            
            # Resolve the route pattern to avoid high cardinality in metrics (e.g. /products/{product_id})
            route = request.scope.get("route")
            if route and hasattr(route, "path"):
                path = route.path
            else:
                path = request.url.path

            http_request_total.labels(
                service_name=self.service_name,
                method=request.method,
                path=path,
                status_code=str(status_code)
            ).inc()

            http_request_duration_seconds.labels(
                service_name=self.service_name,
                method=request.method,
                path=path
            ).observe(duration)
