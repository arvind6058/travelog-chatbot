import sys
import os
import asyncio

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.orchestrator import orchestrator
from app.ai.context import get_conversation_session


async def test_user_exact_7_turn_conversation():
    conv_id = "test_user_7_turn_conversation_flow"
    session = get_conversation_session(conv_id)
    session.clear()

    turns = [
        "I want a 2-day trip to Coorg.",
        "I want to travel from Bangalore.",
        "I have 3 days.",
        "My budget is 7000.",
        "I prefer hills.",
        "I am travelling with 2 people.",
        "Plan the trip for us."
    ]

    print("--- 7-TURN EXACT USER TEST CONVERSATION ---")
    reply = ""
    for i, turn in enumerate(turns, 1):
        res = await orchestrator.process_message(db=None, message=turn, conversation_id=conv_id)
        reply = res.get("reply", "")
        intent = res.get("intent", "")
        print(f"Turn {i}: '{turn}' -> Intent: {intent}")
        print(f"Current session slots: {session.slots}\n")

    # Assert final conversation state BEFORE final reply check
    assert session.slots.get("origin") == "Bangalore", f"Expected origin Bangalore, got {session.slots.get('origin')}"
    assert session.slots.get("destination") == "Coorg", f"Expected destination Coorg, got {session.slots.get('destination')}"
    assert session.slots.get("duration_days") == 3, f"Expected duration 3, got {session.slots.get('duration_days')}"
    assert session.slots.get("total_budget_inr") == 7000.0 or session.slots.get("budget") == 7000.0, f"Expected budget 7000, got {session.slots}"
    assert session.slots.get("travel_preference") == "hills", f"Expected preference hills, got {session.slots.get('travel_preference')}"
    assert session.slots.get("travelers_count") == 2 or session.slots.get("travellers") == 2, f"Expected travellers 2, got {session.slots}"

    # Assert final reply formatting
    assert "Bangalore · 3 days · 1 traveller" not in reply, f"Must NOT say Bangalore 3 days 1 traveller! Reply snippet: {reply[:300]}"
    assert "Coorg" in reply, f"Expected Coorg in final itinerary reply! Reply snippet: {reply[:300]}"
    assert "3 days" in reply or "3-Day" in reply or "3 Days" in reply, f"Expected 3 days in reply! Reply snippet: {reply[:300]}"
    assert "2 traveller" in reply or "2 travellers" in reply, f"Expected 2 travellers in reply! Reply snippet: {reply[:300]}"

    clean_reply = reply.encode('ascii', 'replace').decode()
    print("Final reply snippet:\n", clean_reply[:500])
    print("\n--- EXACT USER 7-TURN TEST CONVERSATION PASSED 100%! ---")


if __name__ == "__main__":
    asyncio.run(test_user_exact_7_turn_conversation())
