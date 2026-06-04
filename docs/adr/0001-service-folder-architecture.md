# ADR 0001: Service Folder Architecture

## Decision

Use `apps/<service>` as the canonical location for deployable service code.
The legacy import compatibility layer has been removed.

## Context

The project previously carried old compatibility imports during the folder
structure migration. Runtime commands, tests, and documentation now use the
canonical `apps.*` modules, so keeping compatibility aliases adds maintenance
cost without protecting an in-repo caller.

## Target Flow

This diagram captures the intended bounded-context flow for order placement and
payment authorization. It shows the translation layers explicitly:

```mermaid
flowchart LR
    C[Mobile / Web Client] -->|POST /api/v1/orders| G[API Gateway<br/>Auth + Routing + Correlation ID]

    G -->|HTTP Command| O[Order Service<br/>Order Bounded Context]

    O -->|Get trusted price and stock| A[ProductCatalogACL]
    A -->|HTTP GET /quote| P[Product Service<br/>Catalog Bounded Context]
    P -->|Product DTO| A
    A -->|CatalogQuote + Money| O

    O -->|Save order: PENDING_PAYMENT| ODB[(Orders DB)]
    O -->|Publish order.created.v1| MQ[(RabbitMQ<br/>ecommerce.events)]

    MQ -->|order.created.v1| PAY[Payment Service<br/>Payment Bounded Context]
    PAY -->|Provider ACL| PSP[Payment Provider]

    PAY -->|Publish payment.authorized.v1| MQ
    MQ -->|payment.authorized.v1| O

    O -->|Update order: CONFIRMED| ODB
```

The repository implementation does not yet expose every endpoint and event
named in this target flow. Use this as the DDD boundary reference, not as a
claim that the current runtime already matches every box and arrow.
