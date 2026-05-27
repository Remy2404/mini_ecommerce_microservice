# Load Test Report

Date: 2026-05-28

Scope:
- Product listing through the API Gateway.
- Cart item writes with trusted server-side pricing.
- Order creation that enters the payment Saga.

Local validation completed:
- The k6 scenario file is present at `tests/load/k6_ecommerce.js`.
- Repository tests assert the script covers products, cart, orders, and Saga
  endpoints.

Execution note:
- The local machine does not currently expose a `k6` binary. The test script is
  ready to run against the existing Dockerized stack once k6 is installed or a
  one-shot k6 container is approved.
