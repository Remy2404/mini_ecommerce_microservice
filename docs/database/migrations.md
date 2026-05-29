## database migrations

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
