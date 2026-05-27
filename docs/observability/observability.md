# Observability

Services share logging, tracing, and metrics helpers from
`packages.observability`.

## Local Endpoints

- HTTP services expose `/metrics`.
- Prometheus reads `infra/prometheus/prometheus.yml`.
- Grafana dashboards live under `infra/grafana`.
- OTEL collector config lives under `infra/otel/otel-collector-config.yml`.

Logs must include useful request, order, payment, and routing identifiers without
printing secrets, access tokens, passwords, or full authorization headers.
