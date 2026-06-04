from uuid import UUID

from apps.order_service.app.infrastructure.errors.exceptions import ForbiddenError


def _parse_order_id(order_id: str) -> UUID | None:
    try:
        return UUID(order_id)
    except ValueError:
        return None


async def get_order_status(order_id: str, *, user_id: str | None = None) -> str | None:
    from apps.order_service.app.application import services as services_module

    parsed_order_id = _parse_order_id(order_id)
    if parsed_order_id is None:
        return None

    if user_id is not None:
        order = await services_module.get_order_record_by_id(parsed_order_id)
        if order is None:
            return None
        if order.user_id != user_id:
            raise ForbiddenError
        return order.status

    return await services_module.get_order_status_by_id(parsed_order_id)


async def get_all_orders(user_id: str | None = None) -> dict[str, str]:
    from apps.order_service.app.application import services as services_module

    return await services_module.list_order_statuses(user_id=user_id)
