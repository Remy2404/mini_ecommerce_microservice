# Load Testing

`k6_ecommerce.js` exercises product listing, cart writes, order creation, and
the payment Saga entrypoint through the API Gateway.

Run against an already-started stack:

```powershell
k6 run tests/load/k6_ecommerce.js `
  -e BASE_URL=http://localhost:8000 `
  -e AUTH_TOKEN=<gateway-token> `
  -e USER_ID=<test-user-id> `
  -e PRODUCT_ID=<existing-product-id>
```

The thresholds fail the run if error rate is at least 5 percent or p95 latency
exceeds 750 ms.
