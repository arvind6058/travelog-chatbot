import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app

settings = get_settings()


@pytest.mark.asyncio
async def test_admin_authentication_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Invalid login attempt
        bad_res = await client.post(
            "/api/v1/auth/admin/login",
            json={"email": "wrong@travelogix.internal", "password": "WrongPassword!"},
        )
        assert bad_res.status_code == 401

        # 2. Valid admin login attempt
        good_res = await client.post(
            "/api/v1/auth/admin/login",
            json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
        )
        assert good_res.status_code == 200
        data = good_res.json()
        assert data["success"] is True
        assert data["user"]["role"] in ["LOGISTICS_ADMIN", "ADMIN"]
        # The session is delivered as an httpOnly cookie, never in the body.
        assert "token" not in data
        assert client.cookies.get("travelogix_admin_token")

        # 3. Verify session endpoint /me (cookie-based)
        me_res = await client.get("/api/v1/auth/admin/me")
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["authenticated"] is True
        assert me_data["user"]["email"] == settings.ADMIN_EMAIL


@pytest.mark.asyncio
async def test_admin_login_is_rate_limited():
    """Unlimited password guessing used to be possible."""
    from app.core.config import get_settings as _get_settings
    from app.core.rate_limit import RateLimiter

    limiter = RateLimiter(attempts=3, window_seconds=60)
    key = "ratelimit:test:fixed-key"

    for _ in range(3):
        await limiter.hit(key)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as excinfo:
        await limiter.hit(key)
    assert excinfo.value.status_code == 429

    await limiter.reset(key)
    await limiter.hit(key)
