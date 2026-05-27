# Payment Service Migrations

The Payment Service owns `payments_db`. It persists payment attempts and, in
later revisions, Saga inbox/outbox tables for idempotent event handling.

```powershell
uv run alembic -c apps/payment_service/alembic.ini upgrade head
uv run alembic -c apps/payment_service/alembic.ini downgrade base
```
