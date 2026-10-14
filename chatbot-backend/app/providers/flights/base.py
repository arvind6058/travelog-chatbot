from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseFlightProvider(ABC):
    """Abstract Base Class for Flight Providers."""

    @abstractmethod
    def search_flights(self, origin: str, destination: str, travel_date: Optional[str] = None) -> Dict[str, Any]:
        """Search for flights between origin and destination on travel_date."""
        pass

    @abstractmethod
    def get_flight_status(self, flight_number: str) -> Dict[str, Any]:
        """Get live status for a specific flight number."""
        pass
