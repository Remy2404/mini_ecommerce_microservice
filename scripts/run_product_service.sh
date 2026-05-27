#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

HOST="${HOST:-127.0.0.1}"
PORT="${PRODUCT_SERVICE_PORT:-8001}"

exec uv run uvicorn apps.product_service.app.main:app --reload --host "${HOST}" --port "${PORT}"
