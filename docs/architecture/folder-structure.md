# Folder Structure

The canonical service implementation lives under `apps/`. Each service owns its
FastAPI routes, application orchestration, domain exceptions, infrastructure
adapters, schemas, tests, and optional workers.

New code, tests, docs, and local commands import from `apps.*`.

## Service Layers

- `app/api`: FastAPI routes and HTTP-only dependencies.
- `app/application`: use cases and orchestration.
- `app/domain`: pure business exceptions and entities.
- `app/infrastructure`: database, cache, HTTP clients, messaging, and security adapters.
- `app/schemas`: request and response DTOs.
- `workers`: background process entrypoints.

## Shared Packages

- `packages/contracts`: shared API and event language.
- `packages/messaging`: RabbitMQ broker and delivery plumbing.
- `packages/database`: SQLAlchemy engine and session helpers.
- `packages/cache`: Valkey client setup.
- `packages/observability`: logging, metrics, tracing, and HTTP metrics middleware.
- `packages/security`: reusable security helpers.
