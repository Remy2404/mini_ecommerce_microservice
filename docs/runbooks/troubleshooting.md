# Troubleshooting Runbook

## Import Errors

Use canonical imports under `apps.*`. Legacy compatibility imports are no
longer supported.

## Gateway Auth

- `401 Missing bearer token`: auth is enabled and no bearer token was provided.
- `401 Invalid token`: JWT validation or WSO2 introspection failed.
- `503 Authentication service unavailable`: WSO2 JWKS or introspection was not reachable.

## Messaging

Check RabbitMQ queues before starting consumers:

```powershell
task rabbitmq:queues
```
