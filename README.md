## Run docker : `docker compose -f infra/docker-compose.yml up -d`
## Cancel docker : `docker compose -f infra/docker-compose.yml down`

## Run local services with scripts
```bash
bash scripts/run_product_service.sh
bash scripts/run_cart_service.sh
bash scripts/run_order_service.sh
bash scripts/run_payment_service.sh
bash scripts/run_api_gateway.sh
```

Run every local service in one shell:
```bash
bash scripts/run_all_local.sh
```

## Run local services directly
uv run uvicorn services.api_gateway.app.main:app --reload --port 8000
uv run uvicorn services.product_service.main:app --reload --port 8001
uv run uvicorn services.cart_service.main:app --reload --port 8002
uv run uvicorn services.order_service.main:app --reload --port 8003
uv run python -m services.payment_service.consumers


curl.exe -i http://127.0.0.1:8000/health
curl.exe -i http://127.0.0.1:8000/metrics/
curl.exe -i http://127.0.0.1:8000/api/v1/products
curl.exe -i http://127.0.0.1:8000/api/v1/cart/user_123
curl.exe -i http://127.0.0.1:8000/api/v1/orders

## Run test : `uv run pytest tests`
## Run test with coverage : `uv run pytest --cov=services tests`

## API Gateway auth

Local development can run without WSO2 token validation:

### Run with WSO2 auth disabled

```powershell
$env:GATEWAY_AUTH_ENABLED = "false"
uv run uvicorn services.api_gateway.app.main:app --reload --port 8000
curl.exe http://localhost:8000/health
```

Protected local mode validates Bearer tokens against WSO2 Identity Server:

### Run with WSO2 auth enabled

```powershell
$env:GATEWAY_AUTH_ENABLED = "true"
$env:WSO2_BASE_URL = "https://localhost:9443"
$env:WSO2_ISSUER = "https://localhost:9443/oauth2/token"
$env:WSO2_AUDIENCE = "mini-ecommerce-api"
$env:WSO2_JWKS_URL = "https://localhost:9443/oauth2/jwks"
$env:WSO2_INTROSPECTION_URL = "https://localhost:9443/oauth2/introspect"
$env:WSO2_VERIFY_SSL = "false"
$env:WSO2_REQUEST_TIMEOUT_SECONDS = "10"
uv run uvicorn services.api_gateway.app.main:app --reload --port 8000
```

Protected gateway routes require the access token from `/auth/login`:

```text
Authorization: Bearer <access_token>
```

If WSO2 returns an opaque access token, the gateway validates it through the WSO2 introspection endpoint. JWT bearer tokens are still validated through JWKS. In Swagger UI, paste the raw `access_token` value into Authorize; Swagger adds `Bearer` for you. Do not use the `id_token` as the API bearer token.

Swagger also exposes the WSO2 username/password login endpoint:

```powershell
curl.exe -i -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"admin\",\"password\":\"admin\",\"scope\":\"openid profile email\"}"
```

Use `WSO2_VERIFY_SSL=false` only for the default local self-signed WSO2 certificate. Production should run with `GATEWAY_AUTH_ENABLED=true` and `WSO2_VERIFY_SSL=true`. See [docs/wso2-local-setup.md](docs/wso2-local-setup.md) for setup steps.

| Phase                               |                  Status | Meaning                                                               |
| ----------------------------------- | ----------------------: | --------------------------------------------------------------------- |
| Phase 1: Core infra                 |                  ✅ Done | Docker, RabbitMQ, Valkey, OTEL Collector, Jaeger, Prometheus, Grafana |
| Phase 2: Core services              |                  ✅ Done | Product, Cart, Order, Payment services exist and run                  |
| Phase 3: Basic Saga flow            |                  ✅ Done | Product → Cart → Order → Payment → CONFIRMED/CANCELLED works          |
| Phase 4: Metrics + monitoring       |          ✅ done | `/metrics` and Prometheus scrape setup                                |
| Phase 5: API Gateway hardening      |              ✅ done | Gateway exists, but needs route completion, security, logging, tests  |
| Phase 6: Security/auth              | ✅done but Not production-ready | WSO2/JWT, IDOR protection, service-to-service trust not complete      |
| Phase 7: PostgreSQL persistence     |             🔴 Not done | Valkey is still acting like main DB                                   |
| Phase 8: Reliability                |             🔴 Not done | retry, DLQ, idempotency, duplicate event handling                     |
| Phase 9: Transaction safety         |             🔴 Not done | outbox pattern, consistency between DB and RabbitMQ                   |
| Phase 10: Production docs/CI/deploy |             🔴 Not done | README, smoke tests, CI, env guide, deployment hardening              |
