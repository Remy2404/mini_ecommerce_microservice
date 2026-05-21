## Run docker : `docker compose -f infra/docker-compose.yml up -d`
## Cancel docker : `docker compose -f infra/docker-compose.yml down`
## Run order service : `uv run uvicorn services.order_service.main:app --reload --port 8003`
## Run payment service :  `uv run python -m services.payment_service.consumers`
## Run order service : `uv run python -m services.order_service.consumers`