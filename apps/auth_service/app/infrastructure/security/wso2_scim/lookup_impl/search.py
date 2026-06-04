from __future__ import annotations

from .list import filter_wso2_users


def _escape_scim_filter_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


async def search_wso2_users(
    *,
    query: str,
    start_index: int = 1,
    count: int = 25,
    request_id: str | None = None,
) -> dict[str, object]:
    escaped = _escape_scim_filter_value(query)
    scim_filter = f'userName co "{escaped}" or emails co "{escaped}"'
    return await filter_wso2_users(
        filter_query=scim_filter,
        start_index=start_index,
        count=count,
        request_id=request_id,
    )
