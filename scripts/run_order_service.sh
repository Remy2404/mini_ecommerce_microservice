#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

HOST="${HOST:-127.0.0.1}"
PORT="${ORDER_SERVICE_PORT:-8003}"

exec uv run uvicorn apps.order_service.app.main:app --reload --host "${HOST}" --port "${PORT}"
