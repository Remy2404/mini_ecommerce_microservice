"""OpenTelemetry settings."""

from pydantic import Field


class ObservabilitySettings:
    otel_exporter_otlp_endpoint: str = Field(
        ..., validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_exporter_otlp_protocol: str = Field(
        ..., validation_alias="OTEL_EXPORTER_OTLP_PROTOCOL"
    )
    otel_exporter_otlp_headers: str = Field(
        "", validation_alias="OTEL_EXPORTER_OTLP_HEADERS"
    )
    otel_resource_attributes: str = Field(
        ..., validation_alias="OTEL_RESOURCE_ATTRIBUTES"
    )
    otel_traces_sampler: str = Field(
        "parentbased_always_on", validation_alias="OTEL_TRACES_SAMPLER"
    )
