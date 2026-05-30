## database migrations

Alembic migrations are incremental. `upgrade head` applies every unapplied
revision, but it does not reset a database or infer that old tables should be
removed. Tables are dropped only when a later migration explicitly drops them.

Auth Service now treats WSO2 Identity Server as the identity source of truth.
The auth migration chain includes a cleanup revision that removes the legacy
local identity tables from `auth_db`:

- `roles`
- `user_addresses`
- `user_roles`

If your `auth_db` already has those tables, run `task migrate:auth` again after
pulling this migration. Use `task db:reset:auth` only when you intentionally
want to destroy and recreate the local auth database.

Option 1: use the task shortcuts
```bash
task migrate:auth
task migrate:product
task migrate:order
task migrate:payment
task migrate:all
```
Option 2: run Alembic directly
```bash
uv run alembic -c apps/auth_service/alembic.ini upgrade head
uv run alembic -c apps/product_service/alembic.ini upgrade head
uv run alembic -c apps/order_service/alembic.ini upgrade head
uv run alembic -c apps/payment_service/alembic.ini upgrade head
```

If you want a clean database first
```bash
task db:reset:all
task migrate:all
```
or 
```bash
task db:reset:auth
task db:reset:product
task db:reset:order
task db:reset:payment
task migrate:auth
task migrate:product
task migrate:order
task migrate:payment
```
