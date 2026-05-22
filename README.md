## Run docker : `docker compose -f infra/docker-compose.yml up -d`
## Cancel docker : `docker compose -f infra/docker-compose.yml down`
uv run uvicorn services.api_gateway.app.main:app --reload --port 8000
uv run uvicorn services.product_service.main:app --reload --port 8001
uv run uvicorn services.cart_service.main:app --reload --port 8002
uv run uvicorn services.order_service.main:app --reload --port 8003


curl.exe -i http://127.0.0.1:8000/health
curl.exe -i http://127.0.0.1:8000/metrics/
curl.exe -i http://127.0.0.1:8000/api/v1/products
curl.exe -i http://127.0.0.1:8000/api/v1/cart/user_123
curl.exe -i http://127.0.0.1:8000/api/v1/orders

## Run test : `uv run pytest tests`
## Run test with coverage : `uv run pytest --cov=services tests`

| Phase                               |                  Status | Meaning                                                               |
| ----------------------------------- | ----------------------: | --------------------------------------------------------------------- |
| Phase 1: Core infra                 |                  ✅ Done | Docker, RabbitMQ, Valkey, OTEL Collector, Jaeger, Prometheus, Grafana |
| Phase 2: Core services              |                  ✅ Done | Product, Cart, Order, Payment services exist and run                  |
| Phase 3: Basic Saga flow            |                  ✅ Done | Product → Cart → Order → Payment → CONFIRMED/CANCELLED works          |
| Phase 4: Metrics + monitoring       |          ✅ done | `/metrics` and Prometheus scrape setup                                |
| Phase 5: API Gateway hardening      |              🟡 Partial | Gateway exists, but needs route completion, security, logging, tests  |
| Phase 6: Security/auth              | 🔴 Not production-ready | WSO2/JWT, IDOR protection, service-to-service trust not complete      |
| Phase 7: PostgreSQL persistence     |             🔴 Not done | Valkey is still acting like main DB                                   |
| Phase 8: Reliability                |             🔴 Not done | retry, DLQ, idempotency, duplicate event handling                     |
| Phase 9: Transaction safety         |             🔴 Not done | outbox pattern, consistency between DB and RabbitMQ                   |
| Phase 10: Production docs/CI/deploy |             🔴 Not done | README, smoke tests, CI, env guide, deployment hardening              |
