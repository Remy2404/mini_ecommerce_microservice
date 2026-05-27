# Production Readiness Runbook

Before production deployment:

- Use canonical `apps.*` service entrypoints in deployment commands.
- Keep `GATEWAY_AUTH_ENABLED=true`.
- Keep `WSO2_VERIFY_SSL=true`.
- Store WSO2 client secrets outside source control.
- Confirm PostgreSQL migrations and indexes for product, order, and payment tables.
- Confirm RabbitMQ queues, routing keys, and dead-letter handling.
- Run `uv run pytest -q` and `uv run ruff check .`.
