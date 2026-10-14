"""
Test configuration.

The suite previously ran against whatever `DATABASE_URL` pointed at — in
practice the developer's live `backend/travelogix.db`, which the tests then
polluted with registrations and shipments. Every session now runs against a
throwaway database created and seeded here.

Environment variables must be set *before* any `app.*` import, because the
engine and the cached settings are built at import time.
"""
import asyncio
import os
import shutil
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# The throwaway database lives inside the project (a temp directory outside the
# workspace is not reliably writable) and is deleted when the session ends.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_TMP_DIR = _BACKEND_DIR / ".pytest-data"
shutil.rmtree(_TMP_DIR, ignore_errors=True)
_TMP_DIR.mkdir(parents=True, exist_ok=True)
_TEST_DB = _TMP_DIR / "test_travelogix.db"

os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["SQL_ECHO"] = "false"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB.as_posix()}"
os.environ["JWT_SECRET"] = "test_only_jwt_secret_do_not_use_in_production_0123456789"
os.environ["CUSTOMER_SESSION_SECRET"] = "test_customer_session_secret_0123456789"
os.environ["ADMIN_SESSION_SECRET"] = "test_admin_session_secret_0123456789"
os.environ["ADMIN_EMAIL"] = "admin@travelogix.internal"
os.environ["ADMIN_PASSWORD"] = "TestAdminPassword123!"
os.environ["ENABLE_DEMO_ACCOUNTS"] = "true"
# Keep auth rate limiting out of the way of the test suite.
os.environ["AUTH_RATE_LIMIT_ATTEMPTS"] = "10000"
# httpx's ASGI transport sends `Host: test`.
os.environ["ALLOWED_HOSTS"] = "localhost,127.0.0.1,testserver,test"

ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]


def pytest_sessionfinish(session, exitstatus):  # pragma: no cover - teardown
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    """Create the schema, the administrator and demo data once per session."""
    from app.db.init_db import init_db

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(init_db())
    finally:
        loop.close()
    yield


@pytest.fixture
async def client():
    """Anonymous client."""
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def customer_client():
    """Client holding a freshly registered customer session."""
    from app.main import app

    email = f"pytest-{uuid.uuid4().hex[:10]}@example.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/customer/register",
            json={
                "email": email,
                "password": "CustomerPassw0rd!",
                "full_name": "Pytest Customer",
                "phone": "+91 90000 00000",
            },
        )
        assert response.status_code == 200, response.text
        ac.customer_email = email  # type: ignore[attr-defined]
        yield ac


@pytest.fixture
async def admin_client():
    """Client holding an authenticated administrator session."""
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/admin/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert response.status_code == 200, response.text
        yield ac


@pytest.fixture
def sample_shipment_payload():
    """A complete, valid customer shipment request."""
    return {
        "shipper_name": "Bangalore Central Hub",
        "recipient_name": "Goa Port Distribution",
        "package_name": "Electronics & Sensors Box",
        "delivery_type": "STANDARD",
        "origin": "Bangalore",
        "destination": "Goa",
        "weight_kg": 15.5,
        "cost_inr": 1850.0,
        "pickup_date": "2026-10-01",
        "expected_delivery_date": "2026-10-05",
    }
