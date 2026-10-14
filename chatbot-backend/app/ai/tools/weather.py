"""
Weather tool.

Delegates to WeatherProvider, which is honest about having no live feed: known
cities get a clearly-labelled static seasonal reference and unknown cities get the
README "Data unavailable from the configured provider" literal instead of another
city's numbers.
"""
from typing import Dict, Any, Optional

from app.core.config import get_settings
from app.providers.weather import WeatherProvider


def getWeather(location: Optional[str], date_str: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve weather/climate reference for a location."""
    provider = WeatherProvider(mode=get_settings().WEATHER_PROVIDER)
    return provider.get_weather(location=location or "", date_str=date_str)
