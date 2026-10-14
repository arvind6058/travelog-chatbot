"""
Answer-order contract: JSON dataset -> LLM -> RAG.

Every travel request must be resolved in that order:

1. the local JSON dataset (``app/data/*.json``) is consulted first and answers on its
   own when it holds rows for the route/city - no LLM call is allowed to rewrite it;
2. the LLM is asked for general guidance only when the dataset has nothing;
3. the RAG knowledge base answers platform/policy questions.

These tests also pin the short-answer shape the customer chat expects.
"""
import json
from pathlib import Path

import pytest

from app.ai.orchestrator import orchestrator
from app.ai.providers.llm import GeminiProvider

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"

# Cities the expanded dataset covers, for coverage assertions.
REQUIRED_HOTEL_CITIES = {
    "goa", "bangalore", "delhi", "mumbai", "chennai", "hyderabad", "kolkata", "pune",
    "jaipur", "kochi", "mysore", "ooty", "coorg", "hampi", "manali", "shimla",
    "udaipur", "varanasi", "agra", "rishikesh", "pondicherry", "tirupati", "madurai",
    "coimbatore", "trivandrum", "mangalore", "gokarna", "wayanad", "chikmagalur",
    "darjeeling", "amritsar", "ahmedabad",
}


def _load(name):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Dataset shape
# --------------------------------------------------------------------------- #
def test_flights_dataset_covers_major_corridors_both_ways():
    flights = _load("flights.json")
    routes = {(f["origin"], f["destination"]) for f in flights}

    assert len(flights) > 200
    for pair in [
        ("Bangalore", "Delhi"), ("Delhi", "Bangalore"),
        ("Bangalore", "Goa"), ("Goa", "Bangalore"),
        ("Mumbai", "Delhi"), ("Delhi", "Mumbai"),
        ("Bangalore", "Jaipur"), ("Chennai", "Hyderabad"),
        ("Kolkata", "Goa"), ("Mumbai", "Kochi"),
    ]:
        assert pair in routes, f"missing flight route {pair}"

    for f in flights:
        assert f["price"] > 0 and f["price_inr"] == f["price"]
        assert f["departure_time"] and f["arrival_time"]
        assert f["stops"] in (0, 1)


def test_hotels_cover_every_supported_city():
    hotels = _load("hotels.json")
    missing = REQUIRED_HOTEL_CITIES - set(hotels)
    assert not missing, f"hotels.json has no entry for: {sorted(missing)}"

    for city, rows in hotels.items():
        assert rows, f"{city} has no hotels"
        for h in rows:
            assert h["hotel_name"] and h["price_per_night"] > 0


def test_trains_and_buses_cover_both_directions():
    trains = _load("trains.json")
    buses = _load("buses.json")

    for route in ["bangalore-delhi", "delhi-bangalore", "chennai-hyderabad", "bangalore-goa"]:
        assert trains["trains"].get(route), f"trains.json missing {route}"
    for route in ["bangalore-goa", "goa-bangalore", "bangalore-mysore"]:
        assert buses["buses"].get(route), f"buses.json missing {route}"

    # Every train/bus row must carry a usable schedule and a sane fare.
    for rows in trains["trains"].values():
        for t in rows:
            assert t["train_number"] and t["departure"] and t["arrival"]
            assert t["fare"] > 0
    for rows in buses["buses"].values():
        for b in rows:
            assert b["operator"] and b["departure"] and b["arrival"]
            assert b["fare"] > 0

    # Running statuses must exist for the trains/buses we advertise.
    assert len(trains["statuses"]) > 50
    assert len(buses["statuses"]) > 50


def test_weather_entries_carry_a_range_not_a_single_reading():
    weather = _load("weather.json")
    assert len(weather) >= len(REQUIRED_HOTEL_CITIES)
    for city, w in weather.items():
        assert w["condition"], city
        assert "°C" in w["temperature_range"], city
        assert w["clothing_recommendation"], city


# --------------------------------------------------------------------------- #
# Tier 1: dataset answers first, without the LLM
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message, intent, needle",
    [
        ("Show flights from Bangalore to Delhi", "FLIGHT_SEARCH", "Flights (Bangalore → Delhi)"),
        ("Show flights from Bangalore to Jaipur", "FLIGHT_SEARCH", "Flights (Bangalore → Jaipur)"),
        ("Hotels in Jaipur", "HOTEL_SEARCH", "Stays in Jaipur"),
        ("Find trains from Chennai to Hyderabad", "TRAIN_SEARCH", "Train Schedules (Chennai → Hyderabad)"),
        ("Bus from Bangalore to Goa", "BUS_SEARCH", "Bus Options (Bangalore → Goa)"),
        ("What is the weather in Bangalore?", "WEATHER_INQUIRY", "Bangalore:"),
        ("How far is Bangalore from Mysore?", "MAPS_ROUTE", "Bangalore → Mysore"),
    ],
)
async def test_dataset_hit_answers_without_the_llm(message, intent, needle, monkeypatch):
    """A dataset hit is served from JSON: the LLM tier is never reached."""
    called = {"count": 0}

    async def _explode(*args, **kwargs):  # pragma: no cover - must not run
        called["count"] += 1
        raise AssertionError("the LLM tier must not run when the dataset has rows")

    monkeypatch.setattr("app.ai.orchestrator.synthesize_with_llm", _explode)

    res = await orchestrator.process_message(message=message)
    assert res["intent"] == intent
    assert res["provenance"]["mode"] == "json"
    assert needle in res["reply"]
    assert called["count"] == 0


@pytest.mark.asyncio
async def test_dataset_hit_answers_stay_short():
    """Customer answers are capped: a handful of one-line options, not a full dump."""
    res = await orchestrator.process_message(message="Show flights from Bangalore to Delhi")
    lines = [line for line in res["reply"].splitlines() if line.strip().startswith("- **")]
    assert 1 <= len(lines) <= 4
    assert len(res["reply"]) < 600


@pytest.mark.asyncio
async def test_dataset_rows_are_never_rewritten_by_a_model(monkeypatch):
    """The values the customer sees are the values in the JSON file."""
    flights = _load("flights.json")
    delhi_fares = {
        f"₹{f['price']:,}" for f in flights
        if f["origin"] == "Bangalore" and f["destination"] == "Delhi"
    }

    async def _explode(*args, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("the LLM tier must not run when the dataset has rows")

    monkeypatch.setattr("app.ai.orchestrator.synthesize_with_llm", _explode)
    res = await orchestrator.process_message(message="Show flights from Bangalore to Delhi")

    shown = {token for token in res["reply"].split() if token.startswith("₹")}
    shown = {t.rstrip(".,") for t in shown}
    assert shown, res["reply"]
    assert shown <= {f.replace(" ", "") for f in delhi_fares} | {
        f.replace("₹", "₹") for f in delhi_fares
    }


# --------------------------------------------------------------------------- #
# Tier 2 and 3: fallbacks, in order
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_unknown_route_falls_to_the_llm_tier(monkeypatch):
    """A route with no dataset rows reaches the LLM tier, and says it is general guidance."""
    seen = {}

    async def _fake_llm(tool_name, tool_result, user_query, history=None):
        seen["tool_name"] = tool_name
        return "Typically there are a few connections a day on that corridor."

    monkeypatch.setattr("app.ai.orchestrator.synthesize_with_llm", _fake_llm)

    res = await orchestrator.process_message(message="Flights from Coimbatore to Ranchi")
    assert seen["tool_name"] == "flightSearchGeneral"
    assert res["provenance"]["mode"] in ("llm", "llm_general")
    assert "Not in my local dataset" not in res["reply"]


@pytest.mark.asyncio
async def test_llm_cannot_confirm_a_route_we_have_no_rows_for(monkeypatch):
    """A model claiming the service exists is discarded in favour of the honest miss."""

    async def _inventing_llm(tool_name, tool_result, user_query, history=None):
        return "Flights from Coimbatore to Ranchi are available. Please specify a travel date."

    monkeypatch.setattr("app.ai.orchestrator.synthesize_with_llm", _inventing_llm)

    res = await orchestrator.process_message(message="Flights from Coimbatore to Ranchi")
    assert "are available" not in res["reply"]
    assert "dataset" not in res["reply"].lower()


@pytest.mark.asyncio
async def test_policy_question_is_answered_from_rag(monkeypatch):
    """Platform/policy questions do not need the LLM: the KB text is returned as-is."""

    async def _explode(*args, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("policy text must come from the KB, not a model")

    monkeypatch.setattr("app.ai.orchestrator.synthesize_with_llm", _explode)

    res = await orchestrator.process_message(message="What is TravelLogix's cancellation policy?")
    assert res["intent"] == "POLICY_RAG"
    assert res["provenance"]["mode"] == "rag"
    assert "refund" in res["reply"].lower()


# --------------------------------------------------------------------------- #
# Honesty guards
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_unknown_train_status_is_not_invented(monkeypatch):
    async def _explode(*args, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("an unknown train must not be described by a model")

    monkeypatch.setattr("app.ai.orchestrator.synthesize_with_llm", _explode)

    res = await orchestrator.process_message(message="Running status of train 99999")
    assert res["intent"] == "TRAIN_STATUS"
    assert "No running status" in res["reply"]
    assert "On Time" not in res["reply"]


@pytest.mark.asyncio
async def test_unknown_flight_status_is_not_invented(monkeypatch):
    async def _explode(*args, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("an unknown flight must not be described by a model")

    monkeypatch.setattr("app.ai.orchestrator.synthesize_with_llm", _explode)

    res = await orchestrator.process_message(message="Status of flight ZZ-0000")
    assert res["intent"] == "FLIGHT_STATUS"
    assert "No status" in res["reply"]


def test_gemini_model_fallback_list_ignores_foreign_model_ids():
    """LLM_MODEL may hold another provider's model id; Gemini must not try to call it."""
    provider = GeminiProvider("fake-key", model="qwen/qwen3.8-27b")
    candidates = provider._candidate_models()
    assert candidates
    assert all(name.startswith("gemini-") for name in candidates)
