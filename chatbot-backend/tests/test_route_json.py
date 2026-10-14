"""
Tests for Route / Distance JSON functionality.
Verifies intent classification, origin/destination extraction, typo normalization,
MapsProvider integration, and customer-facing response presentation.
"""
import re

import pytest
from app.ai.intent import detect_intent, IntentType, extract_origin_destination, normalize_text
from app.ai.orchestrator import orchestrator


@pytest.mark.asyncio
async def test_route_distance_queries():
    test_queries = [
        ("How far is Bangalore from Mysore?", "Bangalore", "Mysore"),
        ("How long does it take from Bangalore to Mysore?", "Bangalore", "Mysore"),
        ("What's the fastest route from Bangalore to Mysore?", "Bangalore", "Mysore"),
        ("Distance from Bangalore to Chennai", "Bangalore", "Chennai"),
        ("How far is banglore from Mysore?", "Bangalore", "Mysore"),
        ("Bangalore to Mysore by car", "Bangalore", "Mysore"),
        ("Bangalore to Mysore by bus", "Bangalore", "Mysore"),
    ]

    for query, expected_orig, expected_dest in test_queries:
        intent, entities = detect_intent(query)
        assert intent == IntentType.MAPS_ROUTE, f"Query '{query}' failed intent detection, got {intent}"
        assert entities.get("origin") == expected_orig, f"Query '{query}' got origin {entities.get('origin')}, expected {expected_orig}"
        assert entities.get("destination") == expected_dest, f"Query '{query}' got dest {entities.get('destination')}, expected {expected_dest}"

        res = await orchestrator.process_message(message=query)
        assert res["intent"] == "MAPS_ROUTE"
        assert res["provenance"]["mode"] == "json"

        reply = res["reply"]
        # The route answer leads with the pair, then the distance and the travel time.
        assert f"**{expected_orig} → {expected_dest}:**" in reply
        assert re.search(r"\d+(\.\d+)?\s*km", reply), reply
        assert re.search(r"(estimated time|about)\s*\d", reply), reply
        # Verify internal details are hidden
        assert "maps_provider" not in reply
        assert "is_mock" not in reply
        assert "provenance" not in reply


def test_typo_handling_mysore_bangalore():
    assert normalize_text("banglore") == "bangalore"
    assert normalize_text("mysore") == "mysore"
    assert normalize_text("mysuru") == "mysore"

    orig, dest = extract_origin_destination("How far is banglore from mysuru?")
    assert orig == "Bangalore"
    assert dest == "Mysore"
