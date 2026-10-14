"""
Unit and Integration tests for Travel AI Quick Actions and Conversational Slot Memory.
"""
import pytest
from app.ai.intent import detect_intent, IntentType
from app.ai.orchestrator import orchestrator
from app.ai.context import get_conversation_session


@pytest.mark.asyncio
async def test_quick_action_initial_prompts():
    quick_action_tests = [
        ("Plan a trip", "TRAVEL_ITINERARY", "Sure! Where would you like to travel?"),
        ("Find a route", "MAPS_ROUTE", "Sure! Where are you travelling from and to?"),
        ("Find a hotel", "HOTEL_SEARCH", "Sure! Which city would you like to stay in?"),
        ("Find a train", "TRAIN_SEARCH", "Sure! Where are you travelling from and to?"),
        ("Find a bus", "BUS_SEARCH", "Sure! Where are you travelling from and to?"),
        ("Weather forecast", "WEATHER_INQUIRY", "Sure! Which city would you like the weather for?"),
    ]

    for prompt, expected_intent, expected_reply in quick_action_tests:
        res = await orchestrator.process_message(message=prompt)
        assert res["intent"] == expected_intent, f"Prompt '{prompt}' expected {expected_intent}, got {res['intent']}"
        assert res["reply"] == expected_reply, f"Prompt '{prompt}' expected reply '{expected_reply}', got '{res['reply']}'"
        assert res.get("data", {}).get("clarification_required") is True


@pytest.mark.asyncio
async def test_hotel_quick_action_conversational_flow():
    session_id = "test_hotel_flow_session_456"
    session = get_conversation_session(session_id)
    session.clear()

    # Step 1: Click "Find a Hotel"
    res1 = await orchestrator.process_message(message="Find a hotel", conversation_id=session_id)
    assert res1["reply"] == "Sure! Which city would you like to stay in?"

    # Step 2: Customer replies "Goa"
    res2 = await orchestrator.process_message(message="Goa", conversation_id=session_id)
    assert res2["intent"] == "HOTEL_SEARCH"
    assert "Goa" in res2["reply"]
    # Verify city = Goa is preserved in session slots
    assert session.slots.get("destination") == "Goa" or session.slots.get("location") == "Goa"
