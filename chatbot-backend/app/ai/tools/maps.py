"""Maps/route tools. Distances are locally calculated great-circle estimates."""
from typing import Dict, Any

from app.core.config import get_settings
from app.providers.maps import MapsProvider


def getRoute(origin: str, destination: str, travel_mode: str = "driving") -> Dict[str, Any]:
    """Execute getRoute tool using MapsProvider."""
    provider = MapsProvider(mode=get_settings().MAPS_PROVIDER)
    return provider.get_route(origin=origin, destination=destination, travel_mode=travel_mode)
