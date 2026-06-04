from apps.auth_service.app.infrastructure.security.wso2_scim.lookup_impl import (
    filter_wso2_users as _filter_wso2_users,
    get_wso2_user_by_id as _get_wso2_user_by_id,
)


async def get_wso2_user_by_id(
    user_id: str,
    *,
    request_id: str | None = None,
):
    return await _get_wso2_user_by_id(user_id, request_id=request_id)


async def filter_wso2_users(
    *,
    filter_query: str | None = None,
    attributes: str | None = None,
    excluded_attributes: str | None = None,
    start_index: int = 1,
    count: int = 25,
    domain: str | None = None,
    request_id: str | None = None,
):
    return await _filter_wso2_users(
        filter_query=filter_query,
        attributes=attributes,
        excluded_attributes=excluded_attributes,
        start_index=start_index,
        count=count,
        domain=domain,
        request_id=request_id,
    )


async def search_wso2_users(
    *,
    query: str,
    start_index: int = 1,
    count: int = 25,
    request_id: str | None = None,
):
    escaped = query.replace("\\", "\\\\").replace('"', '\\"')
    return await filter_wso2_users(
        filter_query=f'userName co "{escaped}" or emails co "{escaped}"',
        start_index=start_index,
        count=count,
        request_id=request_id,
    )
