import time
from typing import AsyncGenerator, Dict, Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

_IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")

# Engine creation with sensible pool configuration.
# echo is governed by SQL_ECHO (not DEBUG) because it prints every statement
# *with bound parameters*, i.e. customer addresses, emails and phone numbers.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,
    connect_args={"timeout": 5} if "postgresql" in settings.DATABASE_URL else {}
)


if _IS_SQLITE:
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        """
        SQLite ships with foreign key enforcement OFF, so every FK in the schema
        was decorative. Enforce them now so dangling references fail loudly here
        instead of the moment the project moves to PostgreSQL.
        """
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    @event.listens_for(engine.sync_engine, "connect")
    def _sqlite_busy_timeout(dbapi_connection, _connection_record) -> None:
        """Wait for locks instead of failing instantly as 'database is locked'."""
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA busy_timeout=5000")
        finally:
            cursor.close()


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for obtaining an asynchronous database session.

    Handlers commit their own work before returning. Committing here would run
    *after* the response has already been sent, so a failed commit used to be
    invisible to a client that had been told the write succeeded.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> Dict[str, Any]:
    """
    Test real database connectivity.

    Never claims connected unless a real connection succeeds, and never returns
    driver exception text (it leaks host, user and dialect to anonymous callers).
    """
    start = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "dialect": engine.dialect.name,
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        }
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return {
            "status": "disconnected",
            "dialect": engine.dialect.name,
            "reason": "database connection failed",
        }
