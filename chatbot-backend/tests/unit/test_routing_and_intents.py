import pytest
from app.ai.intent import detect_intent, IntentType
from app.ai.orchestrator import AIOrchestrator
from app.ai.context import get_conversation_session


@pytest.mark.asyncio
async def test_required_intent_routing_cases():
    test_cases = [
        # General & Advice
        ("Can you suggest a destination for a solo trip?", [IntentType.GENERAL_TRAVEL_ADVICE, IntentType.GENERAL_CHAT], None),
        ("What should I consider before choosing a destination?", [IntentType.GENERAL_TRAVEL_ADVICE, IntentType.GENERAL_CHAT], None),
        ("How can I save money while travelling?", [IntentType.GENERAL_TRAVEL_ADVICE, IntentType.GENERAL_CHAT], None),
        ("What should I pack for a vacation?", [IntentType.GENERAL_TRAVEL_ADVICE, IntentType.GENERAL_CHAT, IntentType.PACKING_ASSISTANT], None),
        ("Why is Goa popular?", [IntentType.GENERAL_TRAVEL_ADVICE, IntentType.GENERAL_CHAT], None),
        # Recommendations
        ("I want somewhere peaceful for a short break.", [IntentType.GENERAL_TRAVEL_ADVICE, IntentType.GENERAL_CHAT], None),
        ("Which places are good for nature lovers?", [IntentType.GENERAL_TRAVEL_ADVICE, IntentType.GENERAL_CHAT], None),
        ("Where can I go with my parents?", [IntentType.GENERAL_TRAVEL_ADVICE, IntentType.GENERAL_CHAT], None),
        # Planning
        ("Plan a 3-day trip to Coorg from Bangalore.", [IntentType.TRAVEL_ITINERARY], "Coorg"),
        ("Help me plan a weekend trip to Chikmagalur.", [IntentType.TRAVEL_ITINERARY], "Chikmagalur"),
        ("Create a 5-day itinerary for Goa.", [IntentType.TRAVEL_ITINERARY], "Goa"),
        # Structured
        ("Plan a bus from Bangalore to Chennai.", [IntentType.BUS_SEARCH], "Chennai"),
        ("Find flights from Bangalore to Delhi.", [IntentType.FLIGHT_SEARCH], "Delhi"),
        ("Find hotels in Jaipur.", [IntentType.HOTEL_SEARCH], "Jaipur"),
        # RAG
        ("What is TravelLogix's cancellation policy?", [IntentType.POLICY_RAG], None),
    ]

    for query, allowed_intents, expected_dest in test_cases:
        intent, entities = detect_intent(query)
        assert intent in allowed_intents, f"Query '{query}' expected intent in {allowed_intents}, got {intent}"
        if expected_dest is not None:
            assert entities.get("destination") == expected_dest or entities.get("location") == expected_dest, (
                f"Query '{query}' expected destination {expected_dest}, got {entities.get('destination') or entities.get('location')}"
            )


@pytest.mark.asyncio
async def test_orchestrator_non_itinerary_responses():
    orchestrator = AIOrchestrator()
    session_id = "test_routing_session"
    session = get_conversation_session(session_id)
    session.clear()

    # 1. Peaceful hill destinations near Bangalore -> Should NOT return generic 7-day Bangalore itinerary
    res1 = await orchestrator.process_message(
        message="What are some peaceful hill destinations near Bangalore for a weekend trip?",
        conversation_id=session_id,
    )
    assert res1["intent"] == IntentType.GENERAL_TRAVEL_ADVICE
    assert res1.get("destination") != "Bangalore"
    assert "A typical 7-day plan" not in res1["reply"]

    # 2. Solo trip suggestion -> Should NOT extract 'Solo' as destination
    res2 = await orchestrator.process_message(
        message="Can you suggest a destination for a solo trip?",
        conversation_id=session_id,
    )
    assert res2["intent"] == IntentType.GENERAL_TRAVEL_ADVICE
    assert res2.get("destination") != "Solo"

    # 3. Best time to visit Coorg -> Should answer question, NOT create 7-day itinerary
    res3 = await orchestrator.process_message(
        message="What is the best time to visit Coorg?",
        conversation_id=session_id,
    )
    assert res3["intent"] == IntentType.GENERAL_TRAVEL_ADVICE
    assert "7-day plan" not in res3["reply"]

    # 4. Explicit trip plan -> SHOULD trigger itinerary planner
    res4 = await orchestrator.process_message(
        message="Plan a 2-day trip to Coorg.",
        conversation_id=session_id,
    )
    assert res4["intent"] == IntentType.TRAVEL_ITINERARY
    assert res4["destination"] == "Coorg"


@pytest.mark.asyncio
async def test_multi_turn_context_and_followup():
    orchestrator = AIOrchestrator()
    session_id = "test_multi_turn_session"
    session = get_conversation_session(session_id)
    session.clear()

    # Step 1: Destination
    await orchestrator.process_message(message="I want to visit Coorg.", conversation_id=session_id)
    assert session.slots.get("destination") == "Coorg"

    # Step 2: Duration
    await orchestrator.process_message(message="For 3 days.", conversation_id=session_id)
    assert session.slots.get("duration_days") == 3

    # Step 3: Origin
    await orchestrator.process_message(message="From Bangalore.", conversation_id=session_id)
    assert session.slots.get("origin") == "Bangalore"

    # Step 4: Budget
    await orchestrator.process_message(message="My budget is ₹7,000.", conversation_id=session_id)
    assert session.slots.get("budget") == 7000.0 or session.slots.get("total_budget_inr") == 7000.0

    # Step 5: Travellers
    await orchestrator.process_message(message="I am travelling with my family.", conversation_id=session_id)

    # Step 6: Trigger Plan
    final_plan = await orchestrator.process_message(message="Now plan the trip.", conversation_id=session_id)
    assert final_plan["intent"] == IntentType.TRAVEL_ITINERARY
    assert final_plan["destination"] == "Coorg"
    assert final_plan["duration_days"] == 3

    # Step 7: Follow-up query reusing accumulated slots
    bus_res = await orchestrator.process_message(message="What if I take a bus?", conversation_id=session_id)
    assert bus_res["intent"] == IntentType.BUS_SEARCH
    assert bus_res.get("destination") == "Coorg"

