# Production Readiness

Implemented:

- Service-owned PostgreSQL databases.
- Valkey cart/cache/rate-limit/idempotency split.
- RabbitMQ topic saga events.
- Structured logging with trace context.
- Prometheus HTTP and business metrics.
- OpenTelemetry FastAPI instrumentation.
- Gateway request ID propagation and safe downstream error mapping.
- JWT issuing and local validation path.

Next hardening steps:

- Replace fake payment provider with a real provider adapter.
- Add Alembic migrations per service.
- Add transactional outbox for order/payment event publishing.
- Add dead-letter replay runbooks.
- Add service-to-service authentication.
- Add CI with lint, tests, image build, and dependency scanning.
- Move local compose credentials to secret management for non-local environments.
