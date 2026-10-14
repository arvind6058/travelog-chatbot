from typing import Dict, Any, Optional
from app.core.config import get_settings
from app.providers.availability import provider_mode
from app.providers.flights.base import BaseFlightProvider
from app.providers.flights.mock import MockFlightProvider
from app.providers.flights.aviationstack import AviationstackFlightProvider

class FlightProvider(BaseFlightProvider):
    """
    Flight Provider Factory & Dispatcher.
    Dispatches to AviationstackFlightProvider when FLIGHT_PROVIDER=aviationstack.
    Dispatches to MockFlightProvider when FLIGHT_PROVIDER=mock.
    """

    def __init__(self, mode: Optional[str] = None):
        cfg_mode = (mode or provider_mode("flights") or get_settings().FLIGHT_PROVIDER or "aviationstack").lower().strip()
        self.mode = cfg_mode
        if self.mode == "aviationstack":
            self.impl: BaseFlightProvider = AviationstackFlightProvider()
        else:
            self.impl = MockFlightProvider()

    def search_flights(self, origin: str, destination: str, travel_date: Optional[str] = None) -> Dict[str, Any]:
        return self.impl.search_flights(origin=origin, destination=destination, travel_date=travel_date)

    def get_flight_status(self, flight_number: str) -> Dict[str, Any]:
        return self.impl.get_flight_status(flight_number=flight_number)
