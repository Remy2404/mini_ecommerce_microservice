#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

pids=()

cleanup() {
  if ((${#pids[@]} > 0)); then
    kill "${pids[@]}" 2>/dev/null || true
    wait "${pids[@]}" 2>/dev/null || true
  fi
}

start_service() {
  local name="$1"
  local script="$2"

  echo "Starting ${name}..."
  bash "${SCRIPT_DIR}/${script}" &
  pids+=("$!")
}

trap cleanup EXIT INT TERM

start_service "product service" "run_product_service.sh"
start_service "cart service" "run_cart_service.sh"
start_service "order service" "run_order_service.sh"
start_service "payment service" "run_payment_service.sh"
start_service "api gateway" "run_api_gateway.sh"

wait -n "${pids[@]}"
