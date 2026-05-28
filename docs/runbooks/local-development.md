# Local Development Runbook

Start infrastructure:

```powershell
docker compose -f infra/docker-compose.yml up -d
```

Run services:

```powershell
uv run uvicorn apps.product_service.app.main:app --reload --port 8001
uv run uvicorn apps.cart_service.app.main:app --reload --port 8002
uv run uvicorn apps.order_service.app.main:app --reload --port 8003
uv run uvicorn apps.api_gateway.app.main:app --reload --port 8000
uv run python -m apps.payment_service.workers.payment_worker
uv run python -m apps.order_service.workers.payment_result_worker
```

Use `task run:*` commands when available to avoid duplicate local service
processes.
