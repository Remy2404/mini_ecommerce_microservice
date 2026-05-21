from prometheus_client import Counter, Histogram

http_request_total = Counter(
    "http_request_total",
    "Total number of HTTP requests",
    ["service_name", "method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service_name", "method", "path"],
)

order_created_total = Counter(
    "order_created_total",
    "Total number of created orders",
    ["service_name"],
)

order_confirmed_total = Counter(
    "order_confirmed_total",
    "Total number of confirmed orders",
    ["service_name"],
)

order_cancelled_total = Counter(
    "order_cancelled_total",
    "Total number of cancelled orders",
    ["service_name"],
)

payment_success_total = Counter(
    "payment_success_total",
    "Total number of successful payments",
    ["service_name"],
)

payment_failed_total = Counter(
    "payment_failed_total",
    "Total number of failed payments",
    ["service_name"],
)

rabbitmq_message_published_total = Counter(
    "rabbitmq_message_published_total",
    "Total number of RabbitMQ messages published",
    ["service_name", "routing_key"],
)

rabbitmq_message_consumed_total = Counter(
    "rabbitmq_message_consumed_total",
    "Total number of RabbitMQ messages consumed",
    ["service_name", "routing_key"],
)

valkey_cache_hit_total = Counter(
    "valkey_cache_hit_total",
    "Total number of Valkey cache hits",
    ["service_name", "cache_key"],
)

valkey_cache_miss_total = Counter(
    "valkey_cache_miss_total",
    "Total number of Valkey cache misses",
    ["service_name", "cache_key"],
)
