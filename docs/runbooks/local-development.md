# Local Development Runbook

Start infrastructure:

```powershell
docker compose -f infra/docker-compose.yml up -d
```

Run services:

```powershell
uv run uvicorn apps.api_gateway.app.main:app --reload --port 8000
uv run uvicorn apps.product_service.app.main:app --reload --port 8001
uv run uvicorn apps.cart_service.app.main:app --reload --port 8002
uv run uvicorn apps.order_service.app.main:app --reload --port 8003
uv run uvicorn apps.payment_service.app.main:app --reload --port 8004
uv run uvicorn apps.auth_service.app.main:app --reload --port 8005
uv run python -m apps.payment_service.workers.payment_worker
uv run python -m apps.order_service.workers.payment_result_worker

```

Use `task run:*` commands when available to avoid duplicate local service
processes.

To look up a payment after an order is processed, call:

```http
GET /api/v1/payments/by-order/{order_id}
```

That returns the `payment_id` along with the payment status and amount.
