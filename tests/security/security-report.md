# Security Test Report

Date: 2026-05-28

Covered controls:
- Missing bearer token is rejected.
- Invalid bearer tokens are rejected.
- Inactive WSO2 opaque access tokens are rejected.
- Cart IDOR attempts are blocked at the API Gateway unless the caller is the
  owner or has the `admin` role.
- Client-controlled cart pricing payloads are rejected by schema validation.
- Gateway Valkey-backed rate limiting returns HTTP 429 after the configured
  request budget is exceeded.

Finding:
- No high-confidence regression remains in the covered controls.
