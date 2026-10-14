import time
from typing import Dict, Any, Optional
import redis.asyncio as aioredis
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

redis_client: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    """Get or create singleton async Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=3,
            socket_connect_timeout=3
        )
    return redis_client


async def close_redis() -> None:
    """Close Redis client connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def check_redis_health() -> Dict[str, Any]:
    """
    Test real Redis connectivity.
    Never claims connected unless real Redis ping succeeds.
    """
    start = time.perf_counter()
    client = get_redis()
    try:
        pong = await client.ping()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        if pong:
            return {
                "status": "connected",
                "latency_ms": latency_ms
            }
        return {
            "status": "disconnected",
            "error": "Redis did not reply with PONG"
        }
    except Exception as e:
        # Never return raw driver text: it leaks host, port and credentials.
        logger.warning(f"Redis health check failed: {str(e)}")
        return {
            "status": "disconnected",
            "reason": "redis connection failed"
        }
