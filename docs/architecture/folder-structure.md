# Folder Structure

The canonical service implementation lives under `apps/`. Each service owns its
FastAPI routes, application orchestration, domain exceptions, infrastructure
adapters, schemas, tests, and optional workers.

New code, tests, docs, and local commands import from `apps.*`.

## Service Layers

- `app/api`: FastAPI routes and HTTP-only dependencies.
- `app/application`: use cases and orchestration. Keep it flat unless a
  service has enough code to justify subpackages.
- `app/domain`: pure business exceptions, entities, and policies. Keep the
  default shape flat with `entities.py`, `exceptions.py`, and `policies.py`.
- `app/infrastructure`: database, cache, HTTP clients, messaging, and security adapters.
- `app/schemas`: request and response DTOs.
- `workers`: background process entrypoints.

## Shared Libraries

- `libs/ecommerce-contracts`: shared API and event language.
- `libs/ecommerce-messaging`: RabbitMQ broker and delivery plumbing.
- `libs/ecommerce-database`: SQLAlchemy engine and session helpers.
- `libs/ecommerce-cache`: Valkey client setup.
- `libs/ecommerce-observability`: logging, metrics, tracing, and HTTP metrics middleware.
- `libs/ecommerce-security`: reusable security helpers.
- `libs/ecommerce-config`: shared application settings.
- `libs/ecommerce-errors`: common application errors and handlers.
- `libs/ecommerce-storage`: object storage and image-processing helpers.
