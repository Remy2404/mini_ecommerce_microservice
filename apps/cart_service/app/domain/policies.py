"""Cart Service policy checks."""

from uuid import UUID


def ensure_cart_key(user_id: str) -> str:
    if not user_id:
        raise ValueError("user_id is required")
    return f"cart:{user_id}"


def same_product(left: UUID, right: UUID) -> bool:
    return left == right
