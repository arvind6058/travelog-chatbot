from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.providers.flights.base import BaseFlightProvider
from app.providers.availability import demo_result, unavailable_result

AIRLINE_CODES: Dict[str, str] = {
    "6E": "IndiGo",
    "AI": "Air India",
    "QP": "Akasa Air",
    "SG": "SpiceJet",
    "UK": "Vistara",
    "IX": "Air India Express",
    "G8": "Go First",
    "I5": "AirAsia India",
    "EK": "Emirates",
    "QR": "Qatar Airways",
    "SQ": "Singapore Airlines",
    "LH": "Lufthansa",
}

CITY_ALIASES: Dict[str, str] = {
    "bangalore": "Bangalore",
    "bengaluru": "Bangalore",
    "banglore": "Bangalore",
    "blr": "Bangalore",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "del": "Delhi",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "bom": "Mumbai",
    "goa": "Goa",
    "goi": "Goa",
    "gox": "Goa",
    "chennai": "Chennai",
    "madras": "Chennai",
    "maa": "Chennai",
    "hyderabad": "Hyderabad",
    "hyd": "Hyderabad",
    "kolkata": "Kolkata",
    "ccu": "Kolkata",
    "jaipur": "Jaipur",
    "jai": "Jaipur",
    "pune": "Pune",
    "pnq": "Pune",
}

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

def _load_flights_dataset() -> List[Dict[str, Any]]:
    json_path = DATA_DIR / "flights.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

FLIGHT_DATASET: List[Dict[str, Any]] = _load_flights_dataset()


class MockFlightProvider(BaseFlightProvider):
    """Mock Flight Provider used when FLIGHT_PROVIDER=mock or as structured fallback."""

    @staticmethod
    def _norm_city(city: Optional[str]) -> str:
        if not city:
            return ""
        c = city.strip().lower()
        return CITY_ALIASES.get(c, city.strip().title())

    def search_flights(self, origin: str, destination: str, travel_date: Optional[str] = None) -> Dict[str, Any]:
        orig_clean = self._norm_city(origin) or "Bangalore"
        dest_clean = self._norm_city(destination) or "Delhi"

        # Filter dataset matching origin and destination
        matched = [
            f for f in FLIGHT_DATASET
            if self._norm_city(f["origin"]).lower() == orig_clean.lower()
            and self._norm_city(f["destination"]).lower() == dest_clean.lower()
        ]

        if not matched:
            # If no exact route match, check reverse or fallback dataset match
            matched = [
                f for f in FLIGHT_DATASET
                if orig_clean.lower() in f["origin"].lower()
                and dest_clean.lower() in f["destination"].lower()
            ]

        if not matched:
            return unavailable_result(
                "flights",
                origin=orig_clean,
                destination=dest_clean,
                travel_date=travel_date,
                reason="no_matching_flights_in_dataset",
            )

        # Clone and assign current search parameters
        result_flights = []
        for f in matched:
            item = dict(f)
            item["origin"] = orig_clean
            item["destination"] = dest_clean
            if travel_date:
                item["travel_date"] = travel_date
            result_flights.append(item)

        return demo_result(
            "flights",
            mode="demo",
            origin=orig_clean,
            destination=dest_clean,
            travel_date=travel_date,
            count=len(result_flights),
            flights=result_flights,
            results=result_flights,
        )

    def get_flight_status(self, flight_number: str) -> Dict[str, Any]:
        fl_num = (flight_number or "").upper().replace(" ", "").replace("_", "")

        # Only report a status for a flight the dataset actually holds. The old
        # behaviour invented "AI-101 / On Time / T3 - Gate 12" for ANY input.
        matched = None
        wanted = fl_num.replace("-", "")
        for row in FLIGHT_DATASET:
            if str(row.get("flight_number", "")).upper().replace("-", "") == wanted:
                matched = row
                break

        if not matched:
            return unavailable_result(
                "flights",
                flight_number=fl_num or None,
                reason="no_status_in_dataset",
            )

        return demo_result(
            "flights",
            mode="demo",
            flight_number=matched["flight_number"],
            airline=matched.get("airline") or AIRLINE_CODES.get(fl_num[:2], "Unknown"),
            origin=matched.get("origin"),
            destination=matched.get("destination"),
            route=f"{matched.get('origin', '')} ➔ {matched.get('destination', '')}",
            departure_time=matched.get("departure_time"),
            arrival_time=matched.get("arrival_time"),
            status="On Time",
            gate=f"{matched.get('origin', 'Departure')} - Gate 12",
            notice="Schedule taken from the local flight dataset; live status is not connected.",
        )

