#!/usr/bin/env bash
set -euo pipefail

uv run uvicorn apps.auth_service.app.main:app --reload --port 8005
