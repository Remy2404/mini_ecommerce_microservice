from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from packages.config.settings import settings
from packages.observability.logging import get_logger

logger = get_logger(__name__)

_tracing_configured = False


def setup_tracing(service_name: str, app: FastAPI | None = None) -> None:
    global _tracing_configured

    if _tracing_configured:
        if app is not None:
            FastAPIInstrumentor.instrument_app(app)

        logger.info(
            "Tracing already configured",
            service_name=service_name,
        )
        return

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": settings.service_version,
            "deployment.environment": settings.app_env,
        }
    )

    tracer_provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True,
    )

    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    trace.set_tracer_provider(tracer_provider)

    if app is not None:
        FastAPIInstrumentor.instrument_app(app)

    _tracing_configured = True

    logger.info(
        "OpenTelemetry tracing configured",
        service_name=service_name,
        otel_endpoint=settings.otel_exporter_otlp_endpoint,
    )


def get_tracer(name: str):
    return trace.get_tracer(name)


def add_span_attributes(attributes: Mapping[str, Any]) -> None:
    current_span = trace.get_current_span()

    for key, value in attributes.items():
        if value is not None:
            current_span.set_attribute(key, str(value))
