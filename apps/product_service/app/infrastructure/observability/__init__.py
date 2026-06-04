"""Product Service observability helpers."""

from apps.product_service.app.infrastructure.observability.http_metrics import (
    HTTPMetricsMiddleware,
)
from apps.product_service.app.infrastructure.observability.logging import (
    add_trace_context,
    get_logger,
    setup_logging,
)
from apps.product_service.app.infrastructure.observability.metrics import (
    http_request_duration_seconds,
    http_request_total,
    order_cancelled_total,
    order_confirmed_total,
    order_created_total,
    payment_failed_total,
    payment_success_total,
    rabbitmq_message_consumed_total,
    rabbitmq_message_published_total,
    valkey_cache_hit_total,
    valkey_cache_miss_total,
)
from apps.product_service.app.infrastructure.observability.tracing import (
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
    "order_cancelled_total",
    "order_confirmed_total",
    "order_created_total",
    "payment_failed_total",
    "payment_success_total",
    "rabbitmq_message_consumed_total",
    "rabbitmq_message_published_total",
    "setup_logging",
    "setup_tracing",
    "valkey_cache_hit_total",
    "valkey_cache_miss_total",
]

