import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_all_customer_chat_prompts():
    test_prompts = [
        ("Plan a 5 day trip to Goa.", "TRAVEL_ITINERARY"),
        ("planne days 5 trip goa", "TRAVEL_ITINERARY"),
        ("Find flights from Bangalore to Goa.", "FLIGHT_SEARCH"),
        ("Find hotels in Goa under ₹3000.", "HOTEL_SEARCH"),
        ("Find trains from Bangalore to Goa.", "TRAIN_SEARCH"),
        ("Find overnight buses from Bangalore to Goa.", "BUS_SEARCH"),
        ("What is the weather in Goa?", "WEATHER_INQUIRY"),
        ("How far is Goa airport from Baga?", "MAPS_ROUTE"),
        ("Plan Goa for 2 people under ₹35000.", "BUDGET_CALCULATION"),
        ("Track TLX-2026-100001.", "SHIPMENT_TRACKING"),
        ("Show my shipments.", "SHIPMENT_TRACKING"),
        ("I want to register a shipment.", "SHIPMENT_REGISTER"),
        ("What is your cancellation policy?", "POLICY_RAG"),
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for prompt, expected_intent in test_prompts:
            response = await client.post(
                "/api/v1/chat",
                json={"message": prompt}
            )
            assert response.status_code == 200, f"Failed for prompt '{prompt}': {response.text}"
            data = response.json()
            assert data["success"] is True
            assert "reply" in data
            assert len(data["reply"]) > 0
            assert data["intent"] == expected_intent, f"Prompt '{prompt}' classified as '{data['intent']}', expected '{expected_intent}'"
