'''Intent-routing regression probe.

Run from backend/:  .\.venv\Scripts\python.exe ..\scratch\intent_regression.py

Prints a MESSAGE / INTENT / DESTINATION / DURATION table for the exact strings
called out in the defect report plus the routing cases asserted by the API suite.
'''
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
sys.stdout.reconfigure(encoding="utf-8")

from app.ai.intent import detect_intent  # noqa: E402

# (message, expected intent, expected destination sentinel)
# "!" means "must NOT be a blank/None placeholder" (checked separately below)
CASES = [
    ("help me plan a trip for one person", "GENERAL_CHAT", None),
    ("can you make a plan for me", "GENERAL_CHAT", None),
    ("I need to plan a vacation", "GENERAL_CHAT", None),
    ("I want to travel to Paris", "TRAVEL_ITINERARY", "Paris"),
    ("what can you help me plan?", "GENERAL_CHAT", None),
    ("where is my flight AI 582?", "FLIGHT_STATUS", None),
    ("train status", "TRAIN_STATUS", None),
    ("running status of 17309", "TRAIN_STATUS", None),
    ("bus status", "BUS_STATUS", None),
    ("what is the weather like today?", "GENERAL_CHAT", None),
    ("hello", "GENERAL_CHAT", None),
    ("thanks!", "GENERAL_CHAT", None),
    ("Good morning", "GENERAL_CHAT", None),
    ("plan 5 days trip goa", "TRAVEL_ITINERARY", "Goa"),
    ("planne days 5 trip goa", "TRAVEL_ITINERARY", "Goa"),
    ("5 day trip to Goa", "TRAVEL_ITINERARY", "Goa"),
    ("make a Goa itinerary", "TRAVEL_ITINERARY", "Goa"),
    ("Plan 3 days in Goa", "TRAVEL_ITINERARY", "Goa"),
    ("Plan a 5 day trip to Goa.", "TRAVEL_ITINERARY", "Goa"),
    ("track TLX-2026-12345678", "SHIPMENT_TRACKING", None),
    ("Track TLX-2026-100001.", "SHIPMENT_TRACKING", None),
    ("Show my shipments.", "SHIPMENT_TRACKING", None),
    ("what is the weather in Goa?", "WEATHER_INQUIRY", "Goa"),
    ("Find flights from Bangalore to Goa.", "FLIGHT_SEARCH", "Goa"),
    ("Find hotels in Goa under ₹3000.", "HOTEL_SEARCH", "Goa"),
    ("Find trains from Bangalore to Goa.", "TRAIN_SEARCH", "Goa"),
    ("Find overnight buses from Bangalore to Goa.", "BUS_SEARCH", "Goa"),
    ("How far is Goa airport from Baga?", "MAPS_ROUTE", None),
    ("Plan Goa for 2 people under ₹35000.", "BUDGET_CALCULATION", "Goa"),
    ("I want to register a shipment.", "SHIPMENT_REGISTER", None),
    ("What is your cancellation policy?", "POLICY_RAG", None),
]

STOPWORD_DESTINATIONS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "single", "couple", "few", "weekend", "me", "my", "plan", "travel",
    "vacation", "holiday", "trip", "tour", "go", "make", "explore", "help",
    "place", "there", "anywhere",
}


def main() -> int:
    failures = []
    print(f"{'MESSAGE':<48} {'INTENT':<20} {'DEST':<12} {'DAYS':<5} ENTITIES")
    print("-" * 130)
    for message, want_intent, want_dest in CASES:
        intent, entities = detect_intent(message)
        dest = entities.get("destination") or entities.get("location")
        days = entities.get("duration_days")
        shown = {k: v for k, v in entities.items() if v is not None}
        print(f"{message[:46]:<48} {intent.value:<20} {str(dest):<12} {str(days):<5} {shown}")
        if intent.value != want_intent:
            failures.append(f"{message!r}: intent {intent.value} != {want_intent}")
        if want_dest is not None and dest != want_dest:
            failures.append(f"{message!r}: destination {dest!r} != {want_dest!r}")
        if want_dest is None and want_intent in ("GENERAL_CHAT", "SHIPMENT_TRACKING",
                                                 "FLIGHT_STATUS", "TRAIN_STATUS",
                                                 "BUS_STATUS", "SHIPMENT_REGISTER",
                                                 "POLICY_RAG"):
            if entities.get("destination") is not None:
                failures.append(f"{message!r}: unexpected destination {entities.get('destination')!r}")
        if entities.get("destination") is not None and str(entities["destination"]).lower() in STOPWORD_DESTINATIONS:
            failures.append(f"{message!r}: destination is a stopword/verb: {entities.get('destination')!r}")

    print()
    # Explicit fabrication checks from the defect report.
    fabricated = {
        "what can you help me plan?": ("Goa", 5),
        "I need to plan a vacation": ("Goa", 5),
        "can you make a plan for me": ("Me", None),
        "help me plan a trip for one person": ("One", None),
        "I want to travel to Paris": ("Travel", None),
        "where is my flight AI 582?": ("6E-2041", None),
        "train status": (None, None),
        "what is the weather like today?": ("Goa", None),
    }
    for message, (bad_dest, bad_days) in fabricated.items():
        intent, entities = detect_intent(message)
        if bad_dest is not None and entities.get("destination") == bad_dest:
            failures.append(f"{message!r}: still fabricates destination {bad_dest!r}")
        if bad_days is not None and entities.get("duration_days") == bad_days:
            failures.append(f"{message!r}: still fabricates duration_days {bad_days}")
        for key, bad in (("flight_number", "6E-2041"), ("train_number", "17309")):
            if entities.get(key) == bad and bad not in message:
                failures.append(f"{message!r}: still fabricates {key}={bad!r}")

    print(f"checks: {len(CASES)} routing cases + {len(fabricated)} fabrication cases")
    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nALL INTENT CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
