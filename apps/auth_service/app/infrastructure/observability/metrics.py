"""Prometheus metrics used by Auth Service."""

from prometheus_client import REGISTRY, Counter, Histogram


def _reuse_or_create_counter(
    name: str,
    documentation: str,
    labelnames: list[str],
):
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
