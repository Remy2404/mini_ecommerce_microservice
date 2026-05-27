import json
from uuid import UUID

from app.services.order_service.repository import (
    clear_orders,
    get_order_status_by_id,
    list_order_statuses,
    update_order_status,
)


def _parse_order_id(order_id: str) -> UUID | None:
    try:
        return UUID(order_id)
    except ValueError:
        return None


async def save_order_status(order_id: str, status: str) -> None:
    parsed_order_id = _parse_order_id(order_id)
    if parsed_order_id is None:
        return

    await update_order_status(parsed_order_id, status)


async def get_order_status(order_id: str) -> str | None:
    parsed_order_id = _parse_order_id(order_id)
    if parsed_order_id is None:
        return None

    return await get_order_status_by_id(parsed_order_id)


async def get_all_orders() -> dict[str, str]:
    return await list_order_statuses()


async def clear_order_state() -> None:
    await clear_orders()


async def dump_order_state() -> str:
    return json.dumps(
        await get_all_orders(),
        indent=2,
        sort_keys=True,
    )
