import json

from apps.order_service.app.application.orders.queries import get_all_orders


async def clear_order_state() -> None:
    from apps.order_service.app.application import services as services_module

    await services_module.clear_orders()


async def dump_order_state() -> str:
    return json.dumps(
        await get_all_orders(),
        indent=2,
        sort_keys=True,
    )
