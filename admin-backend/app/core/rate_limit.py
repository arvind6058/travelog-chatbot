"""
Dependency-free rate limiting for authentication endpoints.

Uses Redis when it is reachable so the limit is shared across workers, and
falls back to a process-local sliding window so the protection still exists on
a single-worker or Redis-less deployment.
"""
import time
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, Request, status

from app.core.config import get_settings
from app.core.logging import logger
from app.core.redis import get_redis


class RateLimiter:
    """Sliding-window limiter keyed by an arbitrary string."""

    def __init__(self, attempts: int, window_seconds: int) -> None:
        self.attempts = max(1, attempts)
        self.window_seconds = max(1, window_seconds)
        self._hits: Dict[str, List[float]] = {}

    # ------------------------------------------------------------------ #
    @staticmethod
    def client_key(request: Request, scope: str, identifier: str = "") -> str:
        """Build a stable key from the caller's address plus an identifier."""
        forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        client = forwarded or (request.client.host if request.client else "unknown")
        return f"ratelimit:{scope}:{client}:{(identifier or '').lower()}"

    def _prune(self, key: str, now: float) -> List[float]:
        cutoff = now - self.window_seconds
        hits = [ts for ts in self._hits.get(key, []) if ts > cutoff]
        self._hits[key] = hits
        return hits

    # ------------------------------------------------------------------ #
    async def _check_redis(self, key: str) -> Optional[Tuple[int, int]]:
        """Return (count, ttl) from Redis, or None when Redis is unavailable."""
        try:
            client = get_redis()
            if client is None:
                return None
            count = await client.incr(key)
            if count == 1:
                await client.expire(key, self.window_seconds)
            ttl = await client.ttl(key)
            return int(count), max(int(ttl), 1)
        except Exception as exc:
            logger.debug(f"Rate limiter falling back to local counters: {exc}")
            return None

    async def hit(self, key: str) -> None:
        """Record an attempt and raise 429 once the window is exhausted."""
        now = time.time()

        redis_result = await self._check_redis(key)
        if redis_result is not None:
            count, ttl = redis_result
            if count > self.attempts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many attempts. Please try again shortly.",
                    headers={"Retry-After": str(ttl)},
                )
            return

        hits = self._prune(key, now)
        if len(hits) >= self.attempts:
            retry_after = int(self.window_seconds - (now - hits[0])) or 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again shortly.",
                headers={"Retry-After": str(max(retry_after, 1))},
            )
        hits.append(now)
        self._hits[key] = hits

        # Opportunistic cleanup so the fallback dict cannot grow forever.
        if len(self._hits) > 2048:
            for stale in [k for k, v in self._hits.items() if not self._prune(k, now)]:
                self._hits.pop(stale, None)

    async def reset(self, key: str) -> None:
        """Clear the counter (called after a successful login)."""
        self._hits.pop(key, None)
        try:
            client = get_redis()
            if client is not None:
                await client.delete(key)
        except Exception:
            pass


def auth_limiter() -> RateLimiter:
    settings = get_settings()
    return RateLimiter(settings.AUTH_RATE_LIMIT_ATTEMPTS, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)


__all__ = ["RateLimiter", "auth_limiter"]
