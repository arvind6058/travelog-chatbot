import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

FORBIDDEN_DEBUG_STRINGS = [
    "AI Orchestrator foundation initialized",
    "Phase 2-8 configured",
    "Provider tools registered",
    "RAG initialized",
    "developer logs",
    "internal development"
]


@pytest.mark.asyncio
async def test_chat_plan_5_days_trip_goa():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={"message": "plan 5 days trip goa"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["intent"] == "TRAVEL_ITINERARY"
        assert data["destination"] == "Goa"
        assert data["duration_days"] == 5

        reply = data["reply"]
        for forbidden in FORBIDDEN_DEBUG_STRINGS:
            assert forbidden not in reply

        assert "Goa" in reply
        assert "Day 1" in reply
        assert "Day 5" in reply


@pytest.mark.asyncio
async def test_chat_planne_days_5_trip_goa_typo():
    """Verify common typos like 'planne days 5 trip goa' are handled cleanly without status messages."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={"message": "planne days 5 trip goa"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["intent"] == "TRAVEL_ITINERARY"
        assert data["destination"] == "Goa"
        assert data["duration_days"] == 5

        reply = data["reply"]
        for forbidden in FORBIDDEN_DEBUG_STRINGS:
            assert forbidden not in reply

        assert "Day 1" in reply
        assert "Day 5" in reply


@pytest.mark.asyncio
async def test_chat_5_day_trip_to_goa():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={"message": "5 day trip to Goa"})
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "TRAVEL_ITINERARY"
        assert data["duration_days"] == 5
        assert "Day 1" in data["reply"]


@pytest.mark.asyncio
async def test_chat_make_a_goa_itinerary():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={"message": "make a Goa itinerary"})
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "TRAVEL_ITINERARY"
        assert "Goa" in data["reply"]
        assert "Day 1" in data["reply"]


@pytest.mark.asyncio
async def test_chat_plan_3_days_in_goa():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={"message": "Plan 3 days in Goa"})
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "TRAVEL_ITINERARY"
        assert data["duration_days"] == 3
        assert "Day 1" in data["reply"]
        assert "Day 3" in data["reply"]


@pytest.mark.asyncio
async def test_chat_track_shipment():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={"message": "track TLX-2026-12345678"})
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "SHIPMENT_TRACKING"
        assert "TLX-2026-12345678" in data["reply"]
        assert "AI Orchestrator foundation initialized" not in data["reply"]


@pytest.mark.asyncio
async def test_chat_weather_in_goa():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={"message": "what is the weather in Goa?"})
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "WEATHER_INQUIRY"
        assert "Weather" in data["reply"] or "Goa" in data["reply"]
        assert "AI Orchestrator foundation initialized" not in data["reply"]
