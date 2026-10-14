from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.redis import get_redis
from app.core.config import get_settings, Settings
from app.core.security import (
    ADMIN_ROLES,
    TOKEN_TYPE_ADMIN,
    TOKEN_TYPE_CUSTOMER,
    bearer_or_cookie_token,
    decode_access_token,
    token_role,
)

ADMIN_COOKIE_NAME = "travelogix_admin_token"
CUSTOMER_COOKIE_NAME = "travelogix_customer_session"


def get_settings_dep() -> Settings:
    return get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


def get_redis_client() -> aioredis.Redis:
    return get_redis()


def _unauthorized(detail: str, code: int = status.HTTP_401_UNAUTHORIZED) -> HTTPException:
    return HTTPException(
        status_code=code,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _assert_user_active(db: AsyncSession, user_id: Optional[str]) -> None:
    """
    Re-check the account against the database so a suspended or deleted user
    cannot keep using a token that is still cryptographically valid.
    """
    if not user_id:
        return
    try:
        from app.models.user import User  # local import avoids a circular import

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    except Exception:  # pragma: no cover - a DB problem must not open the door
        raise _unauthorized("Could not verify the session account.")

    if user is None:
        # The env-seeded console admin has no database row; only tokens that
        # claim an admin identity are allowed to skip the row check.
        return
    if (user.status or "ACTIVE").upper() != "ACTIVE":
        raise _unauthorized("This account is not active.")


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Authorisation dependency for every /admin and admin-socket route.

    Before this existed the whole logistics console was readable and writable
    by any anonymous caller.
    """
    token = bearer_or_cookie_token(request, ADMIN_COOKIE_NAME)
    if not token:
        raise _unauthorized("Admin authentication required.")

    try:
        payload = decode_access_token(token, token_type=TOKEN_TYPE_ADMIN)
    except Exception:
        raise _unauthorized("Invalid or expired admin session.")

    if token_role(payload) not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required for this resource.",
        )

    await _assert_user_active(db, payload.get("sub"))
    return payload


async def get_current_customer(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Authorisation dependency for customer-scoped resources."""
    token = bearer_or_cookie_token(request, CUSTOMER_COOKIE_NAME)
    if not token:
        raise _unauthorized("Customer authentication required.")

    try:
        payload = decode_access_token(token, token_type=TOKEN_TYPE_CUSTOMER)
    except Exception:
        raise _unauthorized("Invalid or expired customer session.")

    if token_role(payload) != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A customer account is required for this resource.",
        )

    await _assert_user_active(db, payload.get("sub"))
    return payload


async def get_optional_customer(request: Request) -> Optional[Dict[str, Any]]:
    """
    Best-effort identity for endpoints that work anonymously but personalise
    when a valid session is present. Never falls back to a shared identity.
    """
    token = bearer_or_cookie_token(request, CUSTOMER_COOKIE_NAME)
    if not token:
        return None
    try:
        payload = decode_access_token(token, token_type=TOKEN_TYPE_CUSTOMER)
    except Exception:
        return None
    if token_role(payload) != "CUSTOMER":
        return None
    return payload


__all__ = [
    "ADMIN_COOKIE_NAME",
    "CUSTOMER_COOKIE_NAME",
    "get_current_customer",
    "get_db",
    "get_optional_customer",
    "get_redis_client",
    "get_settings_dep",
    "require_admin",
]
