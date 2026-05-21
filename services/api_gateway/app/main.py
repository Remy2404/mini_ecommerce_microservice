from fastapi import FastAPI
from app.routers.proxy import router
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware

app = FastAPI(title="API Gateway", version="1.0", redirect_slashes=False)  # ← add this

app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}