# Service Structure Migration Plan

The migration makes `apps/*` the source of truth for deployable service code.

## Steps

1. Move each service implementation into `apps/<service>`.
2. Split modules by layer: API routes, application services, domain exceptions,
   infrastructure adapters, and schemas.
3. Move shared contract definitions into nested `packages/contracts/*` modules
   and keep top-level re-export shims.
4. Update Taskfile, scripts, docs, and tests to use canonical `apps.*` paths.
5. Validate with unit tests, Ruff, and import smoke checks.

## Current State

The legacy compatibility layer has been removed. All in-repo commands,
documentation, and tests should continue to use canonical `apps.*` entrypoints.
