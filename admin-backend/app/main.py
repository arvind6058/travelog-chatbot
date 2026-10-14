from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings
from app.core.logging import logger
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from app.core.redis import close_redis
from app.api.router import api_router
from app.api.v1.health import router as health_router

from app.db.init_db import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown hooks."""
    # Fail fast: never serve traffic with placeholder secrets or DEBUG on.
    settings.validate_runtime()

    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    if not settings.is_production:
        insecure = settings.insecure_secrets()
        if insecure:
            logger.warning(
                "Development mode with placeholder values for: "
                f"{', '.join(insecure)}. Rotate these before deploying."
            )

    try:
        await init_db()
        logger.info("Database initialization completed.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    await close_redis()


app = FastAPI(
    title="TravelLogix Admin Backend",
    version=settings.VERSION,
    description="TravelLogix Admin Logistics Console API Backend",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Reject requests whose Host header we do not serve, so absolute URLs and
# cookies cannot be steered by an attacker-controlled host.
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts_list,
)

# CORS Middleware (explicit allow-list: never wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# Centralized Error Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Root Health Endpoints (Accessible directly at /health, /health/db, /health/redis)
app.include_router(health_router)

# Versioned API V1 Router (/api/v1)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "tagline": "Travel & Logistics in One Chat",
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "status": "operational",
    }
