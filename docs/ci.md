# CI Pipeline

The GitHub Actions workflow at `.github/workflows/ci.yml` runs on pushes and
pull requests to `main`.

Pipeline stages:

1. Install Python and uv with dependency caching keyed by `uv.lock`.
2. Create a local CI `.env` with non-production values.
3. Run `uv run ruff check .`.
4. Run `uv run pytest`.
5. Validate `infra/docker-compose.yml` with `docker compose config --quiet`.
6. Run smoke and end-to-end tests.

The workflow does not publish images or deploy. Secrets used by real
environments must be injected through GitHub environments or a secret manager,
not committed to the repository.
