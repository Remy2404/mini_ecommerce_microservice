from prometheus_client import REGISTRY, Counter, Histogram


def _reuse_or_create_counter(name: str, documentation: str, labelnames: list[str]):
    existing = REGISTRY._names_to_collectors.get(name)  # type: ignore[attr-defined]
    if existing is not None:
        return existing
    try:
        return Counter(name, documentation, labelnames)
    except ValueError:
        existing = REGISTRY._names_to_collectors.get(name)  # type: ignore[attr-defined]
        if existing is None:
            raise
        return existing


def _reuse_or_create_histogram(
    name: str,
    documentation: str,
    labelnames: list[str],
):
    existing = REGISTRY._names_to_collectors.get(name)  # type: ignore[attr-defined]
    if existing is not None:
        return existing
    try:
        return Histogram(name, documentation, labelnames)
    except ValueError:
        existing = REGISTRY._names_to_collectors.get(name)  # type: ignore[attr-defined]
        if existing is None:
            raise
        return existing


http_request_total = _reuse_or_create_counter(
    "http_request_total",
    "Total number of HTTP requests",
    ["service_name", "method", "path", "status_code"],
)

http_request_duration_seconds = _reuse_or_create_histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service_name", "method", "path"],
)

order_created_total = _reuse_or_create_counter(
    "order_created_total",
    "Total number of created orders",
    ["service_name"],
)

order_confirmed_total = _reuse_or_create_counter(
    "order_confirmed_total",
    "Total number of confirmed orders",
    ["service_name"],
)

order_cancelled_total = _reuse_or_create_counter(
    "order_cancelled_total",
    "Total number of cancelled orders",
    ["service_name"],
)

payment_success_total = _reuse_or_create_counter(
    "payment_success_total",
    "Total number of successful payments",
    ["service_name"],
)

payment_failed_total = _reuse_or_create_counter(
    "payment_failed_total",
    "Total number of failed payments",
    ["service_name"],
)

rabbitmq_message_published_total = _reuse_or_create_counter(
    "rabbitmq_message_published_total",
    "Total number of RabbitMQ messages published",
    ["service_name", "routing_key"],
)

rabbitmq_message_consumed_total = _reuse_or_create_counter(
    "rabbitmq_message_consumed_total",
    "Total number of RabbitMQ messages consumed",
    ["service_name", "routing_key"],
)

valkey_cache_hit_total = _reuse_or_create_counter(
    "valkey_cache_hit_total",
    "Total number of Valkey cache hits",
    ["service_name", "cache_key"],
)

valkey_cache_miss_total = _reuse_or_create_counter(
    "valkey_cache_miss_total",
    "Total number of Valkey cache misses",
    ["service_name", "cache_key"],
)
