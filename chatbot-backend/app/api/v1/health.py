from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.db.session import check_db_health
from app.core.redis import check_redis_health

router = APIRouter(tags=["Health"])
settings = get_settings()


# NOTE: this router is mounted twice (unprefixed for /health, and under /api/v1).
# It previously also defined "/" here, which was registered before main.root()
# and shadowed it — that route now lives only in app/main.py.


@router.get("/health", summary="Basic service health check")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }




@router.get("/health/config", summary="Safe OAuth & Service Configuration Health Check")
async def health_config_check() -> Dict[str, Any]:
    from app.services.google_auth_service import GoogleAuthService
    configured = GoogleAuthService.is_configured()
    masked_id = GoogleAuthService.get_masked_client_id()
    secret_set = bool(settings.google_client_secret and "your_google" not in settings.google_client_secret.lower())

    return {
        "backend": "ok",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "google_oauth_configured": configured,
        "google_client_id_configured": configured,
        "google_client_secret_configured": secret_set,
        "google_client_id_masked": masked_id,
        "google_redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }


@router.get("/health/db", summary="Database connection health check")
async def db_health_check() -> JSONResponse:
    result = await check_db_health()
    status_code = status.HTTP_200_OK if result.get("status") == "connected" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=result)


@router.get("/health/redis", summary="Redis cache health check")
async def redis_health_check() -> JSONResponse:
    result = await check_redis_health()
    status_code = status.HTTP_200_OK if result.get("status") == "connected" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=result)


@router.get("/ready", summary="Comprehensive readiness probe")
@router.get("/health/ready", summary="Comprehensive readiness probe")
async def readiness_probe() -> JSONResponse:
    """
    Readiness is gated on the database only.

    Redis is an optional cache/pub-sub layer that the application degrades
    without, so a missing Redis must not mark the whole service unready.
    """
    db_result = await check_db_health()
    redis_result = await check_redis_health()

    is_ready = db_result.get("status") == "connected"
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "ready": is_ready,
            "database": db_result,
            "redis": redis_result,
            "degraded_features": [] if redis_result.get("status") == "connected" else ["realtime_pubsub"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
