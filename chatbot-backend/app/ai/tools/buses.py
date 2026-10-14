"""Bus tools. Live bus tracking/ETA is never fabricated."""
from typing import Dict, Any, Optional

from app.core.config import get_settings
from app.providers.buses import BusProvider


def _provider() -> BusProvider:
    return BusProvider(mode=get_settings().BUS_PROVIDER)


def searchBuses(origin: str, destination: str, bus_type: Optional[str] = None) -> Dict[str, Any]:
    """Execute searchBuses tool using BusProvider."""
    return _provider().search_buses(origin=origin, destination=destination, bus_type=bus_type)


def getBusStatus(bus_identifier: Optional[str]) -> Dict[str, Any]:
    """Execute getBusStatus tool using BusProvider."""
    return _provider().get_bus_status(bus_id_or_operator=bus_identifier or "")
