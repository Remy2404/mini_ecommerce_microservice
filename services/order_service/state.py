import json

from packages.cache.valkey_client import get_valkey_client

ORDER_STATUS_KEY_PREFIX = "order:status"
ORDER_LIST_KEY = "orders:index"


def _order_status_key(order_id: str) -> str:
    return f"{ORDER_STATUS_KEY_PREFIX}:{order_id}"


def save_order_status(order_id: str, status: str) -> None:
    client = get_valkey_client()

    client.set(
        _order_status_key(order_id),
        status,
    )

    client.sadd(
        ORDER_LIST_KEY,
        order_id,
    )


def get_order_status(order_id: str) -> str | None:
    client = get_valkey_client()

    status = client.get(
        _order_status_key(order_id),
    )

    if status is None:
        return None

    return str(status)


def get_all_orders() -> dict[str, str]:
    client = get_valkey_client()

    order_ids = client.smembers(
        ORDER_LIST_KEY,
    )

    orders: dict[str, str] = {}

    for order_id in order_ids:
        status = get_order_status(str(order_id))

        if status is not None:
            orders[str(order_id)] = status

    return orders


def clear_order_state() -> None:
    client = get_valkey_client()

    order_ids = client.smembers(
        ORDER_LIST_KEY,
    )

    keys = [_order_status_key(str(order_id)) for order_id in order_ids]

    if keys:
        client.delete(*keys)

    client.delete(ORDER_LIST_KEY)


def dump_order_state() -> str:
    return json.dumps(
        get_all_orders(),
        indent=2,
        sort_keys=True,
    )
