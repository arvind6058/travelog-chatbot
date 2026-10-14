import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

CUSTOMER_COOKIE = "travelogix_customer_session"


@pytest.mark.asyncio
async def test_customer_authentication_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register a fresh customer
        reg_res = await client.post(
            "/api/v1/auth/customer/register",
            json={
                "email": "testcust@example.com",
                "password": "CustomerSecurePassword123!",
                "full_name": "Test Customer",
                "phone": "+15550199",
            },
        )
        assert reg_res.status_code in (200, 400)
        reg_data = reg_res.json()
        assert "token" not in reg_data  # cookie only
        assert client.cookies.get(CUSTOMER_COOKIE)

        # 2. Invalid credentials are rejected
        bad_res = await client.post(
            "/api/v1/auth/customer/login",
            json={"email": "nonexistent@example.com", "password": "WrongPassword!"},
        )
        assert bad_res.status_code == 401

        # 3. Valid credentials establish a session
        good_res = await client.post(
            "/api/v1/auth/customer/login",
            json={"email": "testcust@example.com", "password": "CustomerSecurePassword123!"},
        )
        assert good_res.status_code == 200
        data = good_res.json()
        assert data["success"] is True
        assert data["user"]["role"] == "CUSTOMER"
        assert client.cookies.get(CUSTOMER_COOKIE)

        # 4. Session check
        me_res = await client.get("/api/v1/auth/customer/me")
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["authenticated"] is True
        assert me_data["user"]["role"] == "CUSTOMER"

        # 5. Logout clears the cookie
        logout = await client.post("/api/v1/auth/customer/logout")
        assert logout.status_code == 200
        me_after = await client.get("/api/v1/auth/customer/me")
        assert me_after.json()["authenticated"] is False


@pytest.mark.asyncio
async def test_hardcoded_demo_backdoor_is_gone(client):
    """
    A fixed email/password pair used to mint a session with no database user.
    Demo accounts are now opt-in via ENABLE_DEMO_ACCOUNTS and never exist in
    production.
    """
    response = await client.post(
        "/api/v1/auth/customer/login",
        json={"email": "user@travelogix.internal", "password": "demo123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_weak_password_is_rejected(client):
    response = await client.post(
        "/api/v1/auth/customer/register",
        json={"email": "weak@example.com", "password": "abc", "full_name": "Weak Password"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_google_oauth_endpoints(client):
    google_login_res = await client.get(
        "/api/v1/auth/customer/google/login", follow_redirects=False
    )
    assert google_login_res.status_code == 302
    location = google_login_res.headers["location"]
    assert "accounts.google.com" in location or "google_oauth_not_configured" in location


@pytest.mark.asyncio
async def test_google_callback_rejects_a_missing_state(client):
    """
    The state check used to fail open: a callback with no state cookie and no
    state parameter was accepted (login CSRF / session fixation).
    """
    response = await client.get(
        "/api/v1/auth/customer/google/callback?code=attacker-supplied-code",
        follow_redirects=False,
    )
    assert response.status_code in (302, 307)
    assert "google_login_failed" in response.headers["location"]
    assert client.cookies.get(CUSTOMER_COOKIE) is None


@pytest.mark.asyncio
async def test_google_callback_rejects_a_mismatched_state(client):
    client.cookies.set("travelogix_oauth_state", "expected-state")
    response = await client.get(
        "/api/v1/auth/customer/google/callback?code=some-code&state=different-state",
        follow_redirects=False,
    )
    assert response.status_code in (302, 307)
    assert "google_login_failed" in response.headers["location"]
