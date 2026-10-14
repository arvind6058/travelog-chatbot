from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.admin import router as admin_router
from app.api.v1.admin_auth import admin_auth_router
from app.api.v1.auth import router as auth_router
from app.api.v1.realtime import router as realtime_router

api_router = APIRouter()

# Register Admin V1 modules
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(admin_auth_router)
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(realtime_router)
