from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.health import router as health_router
from app.api.v1.providers import router as providers_router
from app.api.v1.rag import router as rag_router
from app.api.v1.realtime import router as realtime_router
from app.api.v1.shipments import logistics_router, router as shipments_router

api_router = APIRouter()

# Register Chatbot V1 modules
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(chat_router, prefix="/chat", tags=["AI Chat"])
api_router.include_router(conversations_router)
api_router.include_router(rag_router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(shipments_router)
api_router.include_router(logistics_router)
api_router.include_router(realtime_router)
api_router.include_router(providers_router)


