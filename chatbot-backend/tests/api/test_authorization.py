"""
Regression tests for the authorisation fixes.

Before these changes every /admin route, every /shipments route and the admin
WebSocket accepted anonymous callers.
"""
import pytest

ADMIN_READ_ENDPOINTS = [
    "/api/v1/admin/dashboard",
    "/api/v1/admin/shipments",
    "/api/v1/admin/customers",
    "/api/v1/admin/drivers",
    "/api/v1/admin/vehicles",
    "/api/v1/admin/conversations",
    "/api/v1/admin/audit-logs",
    "/api/v1/admin/reports",
    "/api/v1/admin/delayed-shipments",
    "/api/v1/admin/delivered",
    "/api/v1/admin/tracking/shipments",
    "/api/v1/admin/tracking/drivers",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ADMIN_READ_ENDPOINTS)
async def test_admin_endpoints_reject_anonymous_callers(client, endpoint):
    response = await client.get(endpoint)
    assert response.status_code == 401, f"{endpoint} returned {response.status_code}"


@pytest.mark.asyncio
async def test_admin_write_rejects_anonymous_caller(client):
    response = await client.post(
        "/api/v1/admin/tracking/driver-locations",
        json={"driver_id": "DRV-1001", "latitude": 12.9, "longitude": 77.5},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_customer_token_cannot_reach_admin_api(customer_client):
    """A valid customer session must not open the logistics console."""
    response = await customer_client.get("/api/v1/admin/dashboard")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_admin_session_can_reach_admin_api(admin_client):
    response = await admin_client.get("/api/v1/admin/dashboard")
    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_admin_token_is_not_returned_in_the_body(admin_client):
    """The session must live only in an httpOnly cookie."""
    from app.main import app
    from httpx import ASGITransport, AsyncClient

    from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/admin/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
    assert response.status_code == 200
    assert "token" not in response.json()


@pytest.mark.asyncio
async def test_admin_audit_log_records_the_real_administrator(admin_client):
    response = await admin_client.get("/api/v1/admin/audit-logs?limit=5")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_shipment_list_requires_authentication(client):
    response = await client.get("/api/v1/shipments")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_shipment_list_is_scoped_to_the_caller(customer_client):
    response = await customer_client.get("/api/v1/shipments")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    # A fresh customer owns nothing, and must never see other tenants' freight.
    for shipment in body["shipments"]:
        assert shipment["customer_email"] == customer_client.customer_email


@pytest.mark.asyncio
async def test_public_tracking_never_discloses_customer_pii(client):
    """Anonymous tracking stays available but sanitized."""
    response = await client.get("/api/v1/shipments/TLX-DEMO-100001")
    assert response.status_code == 200
    body = response.json()
    shipment = body["shipment"]
    assert body["access"] == "public"
    for leaked in ("customer_email", "customer_name", "shipper_name", "recipient_name", "cost_inr"):
        assert leaked not in shipment, f"public tracking leaked '{leaked}'"


@pytest.mark.asyncio
async def test_conversation_endpoints_require_authentication(client):
    assert (await client.get("/api/v1/chat/conversations")).status_code == 401


@pytest.mark.asyncio
async def test_customer_cannot_read_another_customers_conversation(customer_client):
    """Ownership is enforced, previously the id alone granted access."""
    response = await customer_client.get("/api/v1/chat/conversations/some-other-conversation")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_websocket_admin_channel_requires_an_admin_token():
    from app.api.v1.realtime import authorise_socket

    assert authorise_socket(None, "admin:all", require_admin=True) is False
    assert authorise_socket("not-a-token", "admin:all", require_admin=True) is False
    assert authorise_socket(None, "admin:all") is False


@pytest.mark.asyncio
async def test_websocket_public_tracking_channel_is_open():
    from app.api.v1.realtime import authorise_socket

    assert authorise_socket(None, "tracking:TLX-DEMO-100001") is True
    # Fleet telemetry is not public.
    assert authorise_socket(None, "drivers:DRV-1001") is False


@pytest.mark.asyncio
async def test_admin_cannot_write_an_invalid_status(admin_client):
    response = await admin_client.patch(
        "/api/v1/admin/shipments/TLX-DEMO-100001", json={"status": "NOT_A_STATUS"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_status_update_requires_a_status(admin_client):
    """A missing status used to write NULL into a NOT NULL column."""
    response = await admin_client.patch("/api/v1/admin/shipments/TLX-DEMO-100001", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_driver_location_coordinates_are_validated(admin_client):
    response = await admin_client.post(
        "/api/v1/admin/tracking/driver-locations",
        json={"driver_id": "DRV-1001", "latitude": 9999, "longitude": -1e308},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_registration_does_not_disclose_account_existence(client):
    """Registering an existing address must not be a user-enumeration oracle."""
    first = await client.post(
        "/api/v1/auth/customer/register",
        json={
            "email": "duplicate@example.com",
            "password": "CustomerPassw0rd!",
            "full_name": "Duplicate Test",
        },
    )
    assert first.status_code == 200

    second = await client.post(
        "/api/v1/auth/customer/register",
        json={
            "email": "duplicate@example.com",
            "password": "CustomerPassw0rd!",
            "full_name": "Duplicate Test",
        },
    )
    assert second.status_code == 400
    assert "already exists" not in second.text.lower()


@pytest.mark.asyncio
async def test_oversized_password_is_rejected_not_a_500(client):
    """bcrypt refuses >72 bytes; that used to surface as an unhandled error."""
    response = await client.post(
        "/api/v1/auth/customer/register",
        json={
            "email": "longpass@example.com",
            "password": "a" * 200,
            "full_name": "Long Password",
        },
    )
    assert response.status_code == 422
