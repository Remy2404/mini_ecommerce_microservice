from fastapi import APIRouter

from apps.api_gateway.app.api.routes.auth.routes import router as auth_router
from apps.api_gateway.app.api.routes.cart.routes import router as cart_router
from apps.api_gateway.app.api.routes.category.routes import router as category_router
from apps.api_gateway.app.api.routes.order.routes import router as order_router
from apps.api_gateway.app.api.routes.payment.routes import router as payment_router
from apps.api_gateway.app.api.routes.product.routes import router as product_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(product_router)
router.include_router(category_router)
router.include_router(cart_router)
router.include_router(order_router)
router.include_router(payment_router)
