FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /workspace
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY packages ./packages
COPY apps ./apps

CMD ["uv", "run", "python", "-m", "apps.payment_service.workers.payment_worker"]
