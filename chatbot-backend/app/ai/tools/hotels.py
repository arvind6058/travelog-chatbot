"""Hotel tools. Mock provider => explicit unavailable result, never invented rates."""
from typing import Dict, Any, Optional

from app.core.config import get_settings
from app.providers.hotels import HotelProvider


def searchHotels(location: str, max_price: Optional[int] = None, keyword: Optional[str] = None) -> Dict[str, Any]:
    """Execute searchHotels tool using HotelProvider."""
    provider = HotelProvider(mode=get_settings().HOTEL_PROVIDER)
    return provider.search_hotels(location=location, max_price=max_price, keyword=keyword)
