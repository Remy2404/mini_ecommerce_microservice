"""Auth Service observability helpers."""

from apps.auth_service.app.infrastructure.observability.http_metrics import (
    HTTPMetricsMiddleware,
)
from apps.auth_service.app.infrastructure.observability.logging import (
    add_trace_context,
    get_logger,
    setup_logging,
)
from apps.auth_service.app.infrastructure.observability.metrics import (
    http_request_duration_seconds,
    http_request_total,
)
from apps.auth_service.app.infrastructure.observability.tracing import (
    add_span_attributes,
    get_tracer,
    setup_tracing,
)

__all__ = [
    "HTTPMetricsMiddleware",
    "add_span_attributes",
    "add_trace_context",
    "get_logger",
    "get_tracer",
    "http_request_duration_seconds",
    "http_request_total",
    "setup_logging",
    "setup_tracing",
]
