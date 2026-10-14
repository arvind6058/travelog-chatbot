"""
Expanded JSON Mode Unit & Integration Tests.

Verifies intent detection, slot extraction, follow-up session continuation,
typo normalization, schema standardization, and customer text presentation.
"""
import pytest
from app.ai.intent import detect_intent, IntentType, normalize_text
from app.ai.context import get_conversation_session, try_resolve_follow_up
from app.ai.orchestrator import orchestrator
from app.ai.normalization import (
    build_json_response,
    normalize_flight,
    normalize_hotel,
    normalize_train,
    normalize_bus,
    normalize_weather,
    normalize_route,
    normalize_cab,
    normalize_shipment,
)
from app.ai.formatting import (
    format_flights_response,
    format_hotels_response,
    format_trains_response,
    format_buses_response,
    format_weather_response,
)


@pytest.mark.asyncio
async def test_1_flight_search():
    res = await orchestrator.process_message(message="Show flights from Bangalore to Delhi")
    assert res["intent"] == "FLIGHT_SEARCH"
    assert "reply" in res
    assert "Bangalore" in res["reply"] or "Delhi" in res["reply"] or "Flight" in res["reply"]


@pytest.mark.asyncio
async def test_2_hotel_search():
    res = await orchestrator.process_message(message="Find hotels in Goa under 5000")
    assert res["intent"] == "HOTEL_SEARCH"
    assert res["destination"] == "Goa"


@pytest.mark.asyncio
async def test_3_train_search():
    res = await orchestrator.process_message(message="Find trains from Bangalore to Delhi on 2026-10-15")
    assert res["intent"] == "TRAIN_SEARCH"


@pytest.mark.asyncio
async def test_4_bus_search():
    res = await orchestrator.process_message(message="Bus from Bangalore to Goa tomorrow")
    assert res["intent"] == "BUS_SEARCH"


@pytest.mark.asyncio
async def test_5_weather():
    res = await orchestrator.process_message(message="What is the weather in Bangalore?")
    assert res["intent"] == "WEATHER_INQUIRY"
    assert res["destination"] == "Bangalore"


@pytest.mark.asyncio
async def test_6_route():
    res = await orchestrator.process_message(message="How far is Bangalore from Mysore?")
    assert res["intent"] == "MAPS_ROUTE"


@pytest.mark.asyncio
async def test_7_shipment_tracking():
    res = await orchestrator.process_message(message="Track TLX-2026-100001")
    assert res["intent"] == "SHIPMENT_TRACKING"
    assert res["tracking_id"] == "TLX-2026-100001"


@pytest.mark.asyncio
async def test_8_follow_up_questions():
    session_id = "test_session_follow_up_123"
    session = get_conversation_session(session_id)
    session.clear()

    # Step 1: Initial query for a route the dataset does not hold, so the bot must
    # ask for the missing date before it can answer.
    res1 = await orchestrator.process_message(
        message="Find trains from Madurai to Kolkata", conversation_id=session_id
    )
    assert res1["intent"] == "TRAIN_SEARCH"
    assert res1.get("data", {}).get("clarification_required") is True

    # Step 2: Follow-up answer with date
    resolved = try_resolve_follow_up("Tomorrow", conversation_id=session_id)
    assert resolved is not None
    intent, slots = resolved
    assert intent == IntentType.TRAIN_SEARCH
    assert slots.get("origin") == "Madurai"
    assert slots.get("destination") == "Kolkata"
    assert slots.get("travel_date") is not None

    res2 = await orchestrator.process_message(
        message="Tomorrow", conversation_id=session_id
    )
    assert res2["intent"] == "TRAIN_SEARCH"


@pytest.mark.asyncio
async def test_8b_dataset_route_needs_no_date_upfront():
    """A route held in the JSON dataset is answered immediately, without asking for a
    date first: the dataset lookup is the first thing every travel request hits."""
    session_id = "test_session_json_first_456"
    get_conversation_session(session_id).clear()

    res = await orchestrator.process_message(
        message="Find trains from Bangalore to Delhi", conversation_id=session_id
    )
    assert res["intent"] == "TRAIN_SEARCH"
    assert res.get("data", {}).get("clarification_required") is None
    assert res["provenance"]["mode"] == "json"
    assert "Train Schedules" in res["reply"]


def test_9_typo_normalization():
    assert normalize_text("banglore") == "bangalore"
    assert normalize_text("hydrabad") == "hyderabad"
    assert normalize_text("chenai") == "chennai"
    assert normalize_text("fligt") == "flight"
    assert normalize_text("hotelss") == "hotels"
    assert normalize_text("trainss") == "trains"
    assert normalize_text("buss") == "bus"
    assert normalize_text("shipmnt") == "shipment"
    assert normalize_text("trak") == "track"


@pytest.mark.asyncio
async def test_10_missing_field_handling():
    res = await orchestrator.process_message(message="Show flights")
    assert res["intent"] == "FLIGHT_SEARCH"
    assert res.get("data", {}).get("clarification_required") is True


@pytest.mark.asyncio
async def test_11_provider_unavailable_handling():
    payload = build_json_response(
        intent="flight_search",
        status="unavailable",
        data=None,
        source="flight_provider",
        data_mode="unavailable",
        message="Current flight data is temporarily unavailable. Please try again.",
    )
    rendered = format_flights_response(payload, "Bangalore", "Delhi")
    assert "temporarily unavailable" in rendered
    assert "flights_provider_unavailable" not in rendered
    assert "provenance" not in rendered


@pytest.mark.asyncio
async def test_12_database_record_not_found():
    res = await orchestrator.process_message(message="Track TLX-0000-000000")
    assert res["intent"] == "SHIPMENT_TRACKING"
    assert "Shipment Not Found" in res["reply"] or "not found" in res["reply"].lower()


def test_13_multiple_search_results():
    items = [
        {"flight_number": "AI101", "airline": "Air India", "price": 4500},
        {"flight_number": "6E202", "airline": "IndiGo", "price": 4200},
    ]
    normalized = [normalize_flight(f) for f in items]
    payload = build_json_response(
        intent="flight_search",
        status="success",
        data={"results": normalized},
    )
    rendered = format_flights_response(payload, "Bangalore", "Delhi")
    assert "AI101" in rendered
    assert "6E202" in rendered


def test_14_booking_url_preservation():
    item = {
        "flight_number": "AI101",
        "booking_url": "https://travelogix.example.com/book/AI101",
    }
    norm = normalize_flight(item)
    assert norm["booking_url"] == "https://travelogix.example.com/book/AI101"
    payload = build_json_response("flight_search", "success", {"results": [norm]})
    rendered = format_flights_response(payload, "Bangalore", "Delhi")
    assert "[Book Flight](https://travelogix.example.com/book/AI101)" in rendered


@pytest.mark.asyncio
async def test_15_json_llm_hybrid_requests():
    res = await orchestrator.process_message(message="Plan a 3 day Goa trip and find hotels under ₹5000")
    assert res["intent"] in ("TRAVEL_ITINERARY", "HOTEL_SEARCH", "BUDGET_CALCULATION")


@pytest.mark.asyncio
async def test_16_rag_json_hybrid_requests():
    res = await orchestrator.process_message(message="What is TravelLogix's travel policy and find me a flight to Delhi?")
    assert res["intent"] in ("POLICY_RAG", "FLIGHT_SEARCH")


@pytest.mark.asyncio
async def test_17_flight_query_variations():
    # 1. Show flights from Bangalore to Delhi
    res1 = await orchestrator.process_message(message="Show flights from Bangalore to Delhi")
    assert res1["intent"] == "FLIGHT_SEARCH"
    assert "Bangalore" in res1["reply"] and "Delhi" in res1["reply"]

    # 2. Find flights from Mumbai to Delhi tomorrow
    res2 = await orchestrator.process_message(message="Find flights from Mumbai to Delhi tomorrow")
    assert res2["intent"] == "FLIGHT_SEARCH"
    assert "Mumbai" in res2["reply"] and "Delhi" in res2["reply"]

    # 3. Are there flights from Bangalore to Goa?
    res3 = await orchestrator.process_message(message="Are there flights from Bangalore to Goa?")
    assert res3["intent"] == "FLIGHT_SEARCH"
    assert "Yes" in res3["reply"] or "Goa" in res3["reply"]

    # 4. Find flights from Chennai to Bangalore
    res4 = await orchestrator.process_message(message="Find flights from Chennai to Bangalore")
    assert res4["intent"] == "FLIGHT_SEARCH"
    assert "Chennai" in res4["reply"] and "Bangalore" in res4["reply"]

    # 5. Show the cheapest flight from Bangalore to Delhi
    res5 = await orchestrator.process_message(message="Show the cheapest flight from Bangalore to Delhi")
    assert res5["intent"] == "FLIGHT_SEARCH"
    assert "AI-101" in res5["reply"] or "4,850" in res5["reply"] or "Bangalore" in res5["reply"]

    # 6. Show flights from banglore to Delhi (typo normalization)
    res6 = await orchestrator.process_message(message="Show flights from banglore to Delhi")
    assert res6["intent"] == "FLIGHT_SEARCH"
    assert "Bangalore" in res6["reply"]

