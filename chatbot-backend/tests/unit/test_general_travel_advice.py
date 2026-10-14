import pytest
from app.ai.intent import detect_intent, IntentType
from app.ai.orchestrator import AIOrchestrator
from app.ai.context import get_conversation_session


@pytest.mark.asyncio
async def test_general_travel_advice_intent_detection():
    cases = [
        "What should I consider before choosing a holiday destination?",
        "What are some things to consider when travelling with elderly parents?",
        "What are some common mistakes people make when planning trips?",
        "I want an inexpensive trip but I don't want to compromise too much on comfort. What should I prioritize?",
        "What should I pack for a vacation?",
        "What should I consider when choosing a hotel?",
        "How can I save money while travelling?",
        "What is important to check before booking a trip?",
        "How do I choose the right destination?",
        "What should I consider when travelling with children?",
    ]
    for case in cases:
        intent, entities = detect_intent(case)
        assert intent == IntentType.GENERAL_TRAVEL_ADVICE, f"Failed for: {case}, got {intent}"
        assert entities.get("destination") is None, f"Destination extracted incorrectly for: {case}"


@pytest.mark.asyncio
async def test_general_travel_advice_orchestrator_execution():
    orchestrator = AIOrchestrator()
    conversation_id = "test_general_advice_conv"
    session = get_conversation_session(conversation_id)
    session.clear()
    
    # 1. Ask general advice
    result = await orchestrator.process_message(
        message="What should I consider before choosing a holiday destination?",
        conversation_id=conversation_id
    )
    assert result["intent"] == IntentType.GENERAL_TRAVEL_ADVICE
    assert result["reply"] is not None and len(result["reply"]) > 0
    assert result.get("destination") is None

    # 2. Start a trip
    result_trip = await orchestrator.process_message(message="I want to visit Coorg for 3 days.", conversation_id=conversation_id)
    assert result_trip["intent"] == IntentType.TRAVEL_ITINERARY
    assert session.slots.get("destination") == "Coorg"

    # 3. Interject with general advice
    result_advice = await orchestrator.process_message(message="What should I consider before choosing activities?", conversation_id=conversation_id)
    assert result_advice["intent"] == IntentType.GENERAL_TRAVEL_ADVICE
    # Stored Coorg slots must remain intact
    assert session.slots.get("destination") == "Coorg"

    # 4. Resume trip planning
    result_resume = await orchestrator.process_message(message="Now plan the trip.", conversation_id=conversation_id)
    assert result_resume["intent"] == IntentType.TRAVEL_ITINERARY
    assert session.slots.get("destination") == "Coorg"
