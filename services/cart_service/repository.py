import json
import valkey
from typing import Optional
from packages.config.settings import settings

client = valkey.Valkey.from_url(
    settings.valkey_url,
    decode_responses=True
)


def health_check():
    return client.ping()


# =========================
# CART OPERATIONS
# =========================

def get_cart(user_id: str) -> Optional[dict]:
    data = client.get(f"cart:{user_id}")

    if not data:
        return None

    return json.loads(data)


def save_cart(user_id: str, cart: dict):
    client.setex(
        f"cart:{user_id}",
        settings.cart_cache_ttl_seconds,  # 🔥 from your config
        json.dumps(cart)
    )


def delete_cart(user_id: str):
    client.delete(f"cart:{user_id}")


# =========================
# BACKUP FOR SAGA
# =========================

def backup_cart(order_id: str, cart: dict):
    client.setex(
        f"cart_backup:{order_id}",
        settings.cart_cache_ttl_seconds,
        json.dumps(cart)
    )


def get_backup_cart(order_id: str):
    data = client.get(f"cart_backup:{order_id}")

    if not data:
        return None

    return json.loads(data)


def clear_backup_cart(order_id: str):
    client.delete(f"cart_backup:{order_id}")