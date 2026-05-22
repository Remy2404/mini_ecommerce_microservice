from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from packages.database.session import get_db

from .repository import OrderRepository
from .schemas import CreateOrderRequest
from .saga import start_order_saga


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@router.post("/")
async def create_order(
    payload: CreateOrderRequest,
    db: AsyncSession = Depends(get_db)
):

    order = await start_order_saga(
        db,
        payload
    )

    return {
        "success": True,
        "message": (
            "Order created "
            "and payment processing started"
        ),
        "data": {
            "order_id": order.id,
            "status": order.status,
            "total_amount": order.total_amount
        }
    }


@router.get("/")
async def list_orders(
    db: AsyncSession = Depends(get_db)
):

    orders = await OrderRepository.get_all(
        db
    )

    return {
        "success": True,
        "message": "Orders fetched successfully",
        "data": [
            {
                "order_id": order.id,
                "user_id": order.user_id,
                "status": order.status,
                "total_amount": order.total_amount
            }
            for order in orders
        ]
    }


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):

    order = await OrderRepository.get_by_id(
        db,
        order_id
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return {
        "success": True,
        "message": "Order fetched successfully",
        "data": {
            "order_id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address
        }
    }