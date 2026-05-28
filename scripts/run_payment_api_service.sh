#!/usr/bin/env bash
set -euo pipefail

uv run uvicorn apps.payment_service.app.main:app --reload --port 8004
