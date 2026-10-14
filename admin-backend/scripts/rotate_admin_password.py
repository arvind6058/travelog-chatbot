"""
Rotate the administrator password in the database.

The console administrator is a real database row, so the stored password is
authoritative — changing ADMIN_PASSWORD in .env will NOT change an existing
account (the application logs a warning when the two disagree).

Usage:
    python scripts/rotate_admin_password.py                      # prompts
    python scripts/rotate_admin_password.py --email a@b.c --password 'NewSecret!23'
"""
import argparse
import asyncio
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import PasswordTooLongError, hash_password, validate_password_length  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402

MIN_PASSWORD_LENGTH = 12


async def rotate(email: str, password: str) -> int:
    try:
        validate_password_length(password)
    except PasswordTooLongError as exc:
        print(f"error: {exc}")
        return 1

    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"error: password must be at least {MIN_PASSWORD_LENGTH} characters.")
        return 1

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        admin = result.scalar_one_or_none()
        if admin is None:
            print(f"error: no account found for '{email}'.")
            return 1

        admin.hashed_password = hash_password(password)
        admin.role = admin.role or "LOGISTICS_ADMIN"
        admin.status = "ACTIVE"
        await session.commit()
        print(f"Updated the password for '{email}'. Existing sessions stay valid until they expire.")

    return 0


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Rotate an administrator password.")
    parser.add_argument("--email", default=settings.ADMIN_EMAIL)
    parser.add_argument("--password", default=None)
    args = parser.parse_args()

    password = args.password
    if not password:
        password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm new password: ")
        if password != confirm:
            print("error: passwords do not match.")
            return 1

    return asyncio.run(rotate(args.email, password))


if __name__ == "__main__":
    raise SystemExit(main())
