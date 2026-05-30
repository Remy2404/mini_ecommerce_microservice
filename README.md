# Mini E-Commerce Microservice Template

Production-style FastAPI backend template with service-owned databases, Valkey,
RabbitMQ saga events, structured logs, Prometheus metrics, and OpenTelemetry
tracing.

## Services

- `apps/auth_service`: users, profiles, addresses, and roles. Access tokens are issued by WSO2.
- `apps/product_service`: categories and products in `products_db`.
- `apps/cart_service`: Valkey cart storage at `cart:{user_id}`.
- `apps/order_service`: orders and order items in `orders_db`.
- `apps/payment_service`: fake payment processing and payments in `payments_db`.
- `apps/api_gateway`: `/api/v1/*` explicit proxy routes, auth, request IDs, rate limiting, metrics.

## Local Development Setup

Before running the application locally, ensure you have the following set up:

### 1. Python Environment

Install uv :

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Create a virtual environment and activate it:

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
uv sync
```

## Run Infra

```powershell
docker compose -f infra/docker-compose.yml up -d
```

Start services locally:

```powershell
uv run uvicorn apps.auth_service.app.main:app --reload --port 8005
uv run uvicorn apps.product_service.app.main:app --reload --port 8001
uv run uvicorn apps.cart_service.app.main:app --reload --port 8002
uv run uvicorn apps.order_service.app.main:app --reload --port 8003
uv run uvicorn apps.payment_service.app.main:app --reload --port 8004
uv run python -m apps.payment_service.workers.payment_worker
uv run python -m apps.order_service.workers.payment_result_worker
uv run uvicorn apps.api_gateway.app.main:app --reload --port 8000
```

Do not start duplicate local processes. Check ports and queue consumers first.

## Test

```powershell
uv run pytest
```

## Main API Gateway Routes

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/categories`
- `GET /api/v1/categories`
- `POST /api/v1/products`
- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`
- `POST /api/v1/cart/items`
- `GET /api/v1/cart/{user_id}`
- `DELETE /api/v1/cart/{user_id}/items/{product_id}`
- `DELETE /api/v1/cart/{user_id}`
- `POST /api/v1/orders`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `GET /api/v1/payments/{payment_id}`

## Documentation

- [Architecture](docs/architecture.md)
- [Database Design](docs/database-design.md)
- [Service Workflow](docs/service-workflow.md)
- [Saga Flow](docs/saga-flow.md)
- [Testing](docs/testing.md)
- [Production Readiness](docs/production-readiness.md)
