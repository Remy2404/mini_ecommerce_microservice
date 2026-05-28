# Architecture

The canonical implementation lives under `apps/<service_name>` and shared
library code lives under `packages`.

Each service follows the same layering:

- `app/api`: FastAPI routes and HTTP dependencies.
- `app/application`: business orchestration and use cases.
- `app/domain`: pure entities, policies, and exceptions.
- `app/infrastructure`: database, Valkey, RabbitMQ, HTTP clients, and security adapters.
- `app/schemas`: request, response, and error DTOs.
- `workers`: background consumers.

The API Gateway exposes explicit `/api/v1/*` routes and never acts as an open
proxy. Product, order, payment, and auth services own their PostgreSQL data.
Cart state, product read cache, rate limiting, and payment idempotency locks use
Valkey. Saga communication uses RabbitMQ topic events.
