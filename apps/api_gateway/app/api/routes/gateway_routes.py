import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from apps.api_gateway.app.api.dependencies import rate_limit, validate_token
from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request
from apps.api_gateway.app.schemas.requests import (
    GatewayAddCartItemRequest,
    GatewayCreateCategoryRequest,
    GatewayCreateOrderRequest,
    GatewayCreateProductRequest,
    GatewayRegisterUserRequest,
    WSO2PasswordLoginRequest,
    swagger_request_body,
)
from apps.api_gateway.app.schemas.responses import (
    DetailErrorResponse,
    GatewayRegisterUserResponse,
    GatewayWso2UserDetailResponse,
    GatewayWso2UsersListResponse,
    WSO2TokenResponse,
)
from packages.config.settings import settings
from packages.errors.exceptions import ForbiddenError
from packages.security.headers import AUTHENTICATED_USER_ID_HEADER
from packages.security.permissions import require_owner_or_role
from packages.security.wso2_login import request_wso2_password_token

router = APIRouter()


def _current_user_id(payload: dict) -> str:
    user_id = str(payload.get("sub") or "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return user_id


def _owner_headers(payload: dict) -> dict[str, str]:
    return {AUTHENTICATED_USER_ID_HEADER: _current_user_id(payload)}


async def _json_body(request: Request) -> dict[str, Any]:
    raw_body = await request.body()
    if not raw_body:
        return {}

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Invalid JSON body") from exc

    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="Request body must be an object")
    return body


async def _owned_body(request: Request) -> bytes:
    body = await _json_body(request)
    if "user_id" in body:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return json.dumps(body, separators=(",", ":")).encode("utf-8")


async def enforce_gateway_access(
    request: Request,
    payload: dict = Depends(validate_token),
) -> dict:
    await rate_limit(request, payload)
    return payload


def enforce_user_scope(payload: dict, resource_user_id: str) -> None:
    if not settings.gateway_auth_enabled:
        return

    try:
        require_owner_or_role(
            resource_owner_id=resource_user_id,
            current_user_id=str(payload.get("sub", "")),
            user_roles=payload.get("roles", []),
            role="admin",
        )
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        ) from exc


@router.get("/products", tags=["Product Gateway"])
async def list_products(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", "", request)


@router.post(
    "/auth/register",
    tags=["WSO2 Gateway"],
    status_code=status.HTTP_201_CREATED,
    response_model=GatewayRegisterUserResponse,
    summary="Register user in WSO2 Identity Server",
    description=(
        "Creates a WSO2 Identity Server user through SCIM2. WSO2 client "
        "credentials stay behind the backend."
    ),
    responses={
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 is unavailable or registration is not configured.",
        },
    },
    openapi_extra=swagger_request_body(GatewayRegisterUserRequest),
)
async def register_user(
    request: Request,
):
    return await forward_request("auth", "register", request)


@router.post(
    "/auth/login",
    tags=["WSO2 Gateway"],
    response_model=WSO2TokenResponse,
    summary="Login via WSO2 Identity Server",
    description=(
        "Authenticates a WSO2 Identity Server user and returns the WSO2 token "
        "response. Use the WSO2 username from registration. Copy the full WSO2 "
        "invitation password exactly, including trailing symbols."
    ),
    responses={
        401: {
            "model": DetailErrorResponse,
            "description": "Invalid username or password.",
        },
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 is unavailable or the gateway WSO2 client is misconfigured.",
        },
    },
)
async def login_user(request: WSO2PasswordLoginRequest) -> dict[str, Any]:
    return await request_wso2_password_token(
        username=request.username,
        password=request.password.get_secret_value(),
        scope=request.scope,
    )


@router.get(
    "/auth/users",
    tags=["WSO2 Gateway"],
    response_model=GatewayWso2UsersListResponse,
    summary="List or filter WSO2 users",
    description=(
        "Proxies to Auth Service WSO2 SCIM2 user listing. Requires a gateway "
        "bearer token when gateway auth is enabled."
    ),
    responses={
        401: {"model": DetailErrorResponse, "description": "Missing or invalid token."},
        403: {"model": DetailErrorResponse, "description": "Insufficient WSO2 scope."},
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 or Auth Service is unavailable.",
        },
    },
)
async def list_wso2_users(
    request: Request,
    filter_: str | None = Query(
        default=None,
        alias="filter",
        description="SCIM2 filter expression.",
    ),
    attributes: str | None = Query(
        default=None,
        description="Comma-separated attributes to include.",
    ),
    excluded_attributes: str | None = Query(
        default=None,
        alias="excludedAttributes",
        description="Comma-separated attributes to exclude.",
    ),
    start_index: int = Query(default=1, ge=1, alias="startIndex"),
    count: int = Query(default=25, ge=1, le=100),
    domain: str | None = Query(default=None, description="WSO2 user store domain."),
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", "users", request)


@router.get(
    "/auth/users/search",
    tags=["WSO2 Gateway"],
    response_model=GatewayWso2UsersListResponse,
    summary="Search WSO2 users",
    description=(
        "Proxies to Auth Service WSO2 user search, which builds a safe SCIM2 "
        "filter from the keyword."
    ),
    responses={
        401: {"model": DetailErrorResponse, "description": "Missing or invalid token."},
        403: {"model": DetailErrorResponse, "description": "Insufficient WSO2 scope."},
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 or Auth Service is unavailable.",
        },
    },
)
async def search_wso2_users(
    request: Request,
    q: str = Query(min_length=1, max_length=255, description="Search term."),
    start_index: int = Query(default=1, ge=1, alias="startIndex"),
    count: int = Query(default=25, ge=1, le=100),
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", "users/search", request)


@router.get(
    "/auth/users/{user_id}",
    tags=["WSO2 Gateway"],
    response_model=GatewayWso2UserDetailResponse,
    summary="Get WSO2 user by SCIM ID",
    description="Proxies to Auth Service WSO2 SCIM2 user detail lookup.",
    responses={
        401: {"model": DetailErrorResponse, "description": "Missing or invalid token."},
        403: {"model": DetailErrorResponse, "description": "Insufficient WSO2 scope."},
        404: {"model": DetailErrorResponse, "description": "User not found."},
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 or Auth Service is unavailable.",
        },
    },
)
async def get_wso2_user(
    user_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("auth", f"users/{user_id}", request)


@router.post(
    "/categories",
    tags=["Category Gateway"],
    status_code=status.HTTP_201_CREATED,
    openapi_extra=swagger_request_body(GatewayCreateCategoryRequest),
)
async def create_category(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("categories", "", request)


@router.get("/categories", tags=["Category Gateway"])
async def list_categories(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("categories", "", request)


@router.post(
    "/products",
    tags=["Product Gateway"],
    status_code=status.HTTP_201_CREATED,
    openapi_extra=swagger_request_body(GatewayCreateProductRequest),
)
async def create_product(
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", "", request)


@router.get("/products/{product_id}", tags=["Product Gateway"])
async def get_product(
    product_id: str,
    request: Request,
    _: dict = Depends(enforce_gateway_access),
):
    return await forward_request("products", product_id, request)


@router.get("/cart/{user_id}", tags=["Cart Gateway"])
async def get_cart(
    user_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    enforce_user_scope(payload, user_id)
    return await forward_request(
        "cart",
        user_id,
        request,
        extra_headers=_owner_headers(payload),
    )


@router.post(
    "/cart/items",
    tags=["Cart Gateway"],
    status_code=status.HTTP_201_CREATED,
    openapi_extra=swagger_request_body(GatewayAddCartItemRequest),
)
async def add_cart_item(
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "cart",
        "items",
        request,
        body_override=await _owned_body(request),
        extra_headers=_owner_headers(payload),
    )


@router.delete("/cart/{user_id}/items/{product_id}", tags=["Cart Gateway"])
async def remove_cart_item(
    user_id: str,
    product_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    enforce_user_scope(payload, user_id)
    return await forward_request(
        "cart",
        f"{user_id}/items/{product_id}",
        request,
        extra_headers=_owner_headers(payload),
    )


@router.delete("/cart/{user_id}", tags=["Cart Gateway"])
async def clear_cart(
    user_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    enforce_user_scope(payload, user_id)
    return await forward_request(
        "cart",
        user_id,
        request,
        extra_headers=_owner_headers(payload),
    )


@router.get("/orders", tags=["Order Gateway"])
async def list_orders(
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "orders",
        "",
        request,
        extra_headers=_owner_headers(payload),
    )


@router.post(
    "/orders",
    tags=["Order Gateway"],
    status_code=status.HTTP_201_CREATED,
    openapi_extra=swagger_request_body(GatewayCreateOrderRequest),
)
async def create_order(
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "orders",
        "",
        request,
        body_override=await _owned_body(request),
        extra_headers=_owner_headers(payload),
    )


@router.get("/orders/{order_id}", tags=["Order Gateway"])
async def get_order(
    order_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "orders",
        order_id,
        request,
        extra_headers=_owner_headers(payload),
    )


@router.get("/payments/{payment_id}", tags=["Payment Gateway"])
async def get_payment(
    payment_id: str,
    request: Request,
    payload: dict = Depends(enforce_gateway_access),
):
    return await forward_request(
        "payments",
        payment_id,
        request,
        extra_headers=_owner_headers(payload),
    )
