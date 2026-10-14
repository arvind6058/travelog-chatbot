import uuid

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import ADMIN_ROLES, hash_password, verify_password
from app.db.base import Base
from app.db.migrate import apply_schema_updates
from app.db.session import engine, AsyncSessionLocal
from app.db.seed_data import seed_initial_data
from app.models.user import User
import app.models  # noqa: F401  (loads every model into Base.metadata)

# Environments that receive demo/sample data.
SEEDING_ENVIRONMENTS = {"development", "dev", "local", "test", "testing"}


async def ensure_admin_user(db) -> None:
    """
    Guarantee that the configured administrator exists as a real database row.

    Administrator authentication is database-backed, so the account must exist
    and must be revocable (previously a plaintext environment password bypassed
    the database entirely and could never be deactivated).
    """
    settings = get_settings()
    email = settings.ADMIN_EMAIL.strip()

    result = await db.execute(select(User).where(User.email == email))
    admin = result.scalar_one_or_none()

    if admin is None:
        db.add(
            User(
                id=str(uuid.uuid4()),
                email=email,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                full_name="TravelLogix Administrator",
                role="LOGISTICS_ADMIN",
                status="ACTIVE",
                is_demo=False,
            )
        )
        await db.commit()
        logger.info(f"Bootstrapped the initial administrator account '{email}'.")
        return

    changed = False
    if admin.role not in ADMIN_ROLES:
        admin.role = "LOGISTICS_ADMIN"
        changed = True
    if (admin.status or "ACTIVE").upper() != "ACTIVE":
        logger.warning(f"Administrator '{email}' is not ACTIVE and cannot sign in.")

    if not verify_password(settings.ADMIN_PASSWORD, admin.hashed_password):
        logger.warning(
            f"ADMIN_PASSWORD does not match the stored password for '{email}'. "
            "The database value is authoritative — rotate it with "
            "'python scripts/rotate_admin_password.py' instead of editing .env."
        )

    if changed:
        await db.commit()


async def init_db():
    """Create all tables, apply additive schema updates, then ensure admin + seed data."""
    settings = get_settings()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all never emits ALTER TABLE, so bring pre-existing databases
        # (and their indexes) up to the current model shape in place.
        await conn.run_sync(apply_schema_updates)

    async with AsyncSessionLocal() as session:
        try:
            await ensure_admin_user(session)
            if settings.ENVIRONMENT.lower() in SEEDING_ENVIRONMENTS:
                await seed_initial_data(session)
                await session.commit()
            else:
                logger.info(
                    f"Skipping demo data seeding for ENVIRONMENT='{settings.ENVIRONMENT}'."
                )
        except Exception as e:
            await session.rollback()
            raise e
