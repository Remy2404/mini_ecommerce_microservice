"""Token adapter for Auth Service."""

def issue_user_token(*args, **kwargs) -> str:
    raise RuntimeError(
        "Local JWT issuance is removed. Use API Gateway /api/v1/auth/login with WSO2.",
    )
