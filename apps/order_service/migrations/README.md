# Order Service Migrations

The Order Service owns `orders_db` and manages order state. Saga event tables
are added in later revisions so order creation can persist business data and
outbox events atomically.

```powershell
uv run alembic -c apps/order_service/alembic.ini upgrade head
uv run alembic -c apps/order_service/alembic.ini downgrade base
```
