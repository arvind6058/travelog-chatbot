"""Shipment registration now requires an authenticated customer."""
import pytest


@pytest.mark.asyncio
async def test_create_shipment_valid(customer_client, sample_shipment_payload):
    response = await customer_client.post("/api/v1/shipments", json=sample_shipment_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert "shipment" in data
    assert data["shipment"]["tracking_id"].startswith("TLX-")
    assert data["shipment"]["status"] == "REGISTERED"
    assert data["shipment"]["origin"] == "Bangalore"
    assert data["shipment"]["destination"] == "Goa"
    # The owning identity comes from the session, never the body.
    assert data["shipment"]["customer_email"] == customer_client.customer_email


@pytest.mark.asyncio
async def test_create_shipment_invalid_dates(customer_client, sample_shipment_payload):
    payload = dict(sample_shipment_payload)
    payload["pickup_date"] = "2026-10-10"
    payload["expected_delivery_date"] = "2026-10-01"

    response = await customer_client.post("/api/v1/shipments", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_shipment_requires_authentication(client, sample_shipment_payload):
    """Anonymous freight injection must be rejected."""
    response = await client.post("/api/v1/shipments", json=sample_shipment_payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_shipment_rejects_unvalidated_fields(customer_client, sample_shipment_payload):
    """Fleet assignment and demo flags cannot be injected through the body."""
    payload = dict(sample_shipment_payload)
    payload["assigned_driver_id"] = "some-driver"
    payload["is_demo"] = True

    response = await customer_client.post("/api/v1/shipments", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_shipment_rejects_malformed_dates(customer_client, sample_shipment_payload):
    """Dates used to be free-form strings compared lexicographically."""
    payload = dict(sample_shipment_payload)
    payload["pickup_date"] = "01/02/2026"
    payload["expected_delivery_date"] = "2026-1-5"

    response = await customer_client.post("/api/v1/shipments", json=payload)
    assert response.status_code == 422
