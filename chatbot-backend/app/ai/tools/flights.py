"""
Flight tools.

Every function returns the provider payload unchanged so the orchestrator can see
the provenance/availability flags. When no live flight backend is configured the
provider returns the README "Data unavailable from the configured provider"
literal instead of sample schedules.
"""
from typing import Dict, Any, Optional

from app.core.config import get_settings
from app.providers.flights import FlightProvider


def _provider() -> FlightProvider:
    return FlightProvider(mode=get_settings().FLIGHT_PROVIDER)


def searchFlights(origin: str, destination: str, travel_date: Optional[str] = None) -> Dict[str, Any]:
    """Execute searchFlights tool using FlightProvider."""
    return _provider().search_flights(origin=origin, destination=destination, travel_date=travel_date)


def getFlightStatus(flight_number: Optional[str]) -> Dict[str, Any]:
    """Execute getFlightStatus tool using FlightProvider."""
    return _provider().get_flight_status(flight_number=flight_number or "")
