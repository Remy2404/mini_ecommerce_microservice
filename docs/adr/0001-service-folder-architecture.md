# ADR 0001: Service Folder Architecture

## Decision

Use `apps/<service>` as the canonical location for deployable service code.
The legacy import compatibility layer has been removed.

## Context

The project previously carried old compatibility imports during the folder
structure migration. Runtime commands, tests, and documentation now use the
canonical `apps.*` modules, so keeping compatibility aliases adds maintenance
cost without protecting an in-repo caller.

## Consequences

- New code uses `apps.*` imports.
- Legacy compatibility imports are unsupported.
- Shared contracts live under nested `packages/contracts/*` modules with
  top-level re-export shims.
- External commands and deployments must use canonical `apps.*` entrypoints.
