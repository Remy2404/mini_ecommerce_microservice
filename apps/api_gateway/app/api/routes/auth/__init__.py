from fastapi import APIRouter

from apps.api_gateway.app.api.routes.auth.login import router as login_router
from apps.api_gateway.app.api.routes.auth.register import router as register_router
from apps.api_gateway.app.api.routes.auth.users import router as users_router

router = APIRouter()
router.include_router(register_router)
router.include_router(login_router)
router.include_router(users_router)
