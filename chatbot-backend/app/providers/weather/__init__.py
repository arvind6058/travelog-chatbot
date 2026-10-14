from typing import Dict, Any, Optional

from app.providers.availability import (
    demo_result,
    is_live_provider,
    provider_mode,
    unavailable_result,
)

# Cities for which this build ships a static seasonal climate note. Everything
# else must ask/return unavailable - the old code silently answered with Goa
# numbers ("Fair & Clear", "22°C - 30°C") for ANY unknown city.
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

def _load_weather_dataset() -> Dict[str, Dict[str, str]]:
    json_path = DATA_DIR / "weather.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

KNOWN_CLIMATE: Dict[str, Dict[str, str]] = _load_weather_dataset()

CLIMATE_NOTICE = (
    "Static seasonal climate reference for this city - not a live weather feed."
)


class WeatherProvider:
    """
    Weather provider adapter.

    No live meteorological upstream is configured (WEATHER_PROVIDER=mock), so this
    provider never claims a live forecast. It returns a clearly-labelled static
    seasonal reference for known cities and the unavailable literal for everything
    else instead of echoing another city's numbers.
    """

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or provider_mode("weather") or "demo").lower()

    @property
    def is_live(self) -> bool:
        return is_live_provider("weather")

    def get_weather(self, location: str, date_str: Optional[str] = None) -> Dict[str, Any]:
        loc_clean = (location or "").strip()

        if not loc_clean:
            return unavailable_result("weather", location=None, reason="no_location_supplied")

        if self.is_live:
            # A live adapter would call the configured upstream here.
            return unavailable_result(
                "weather",
                location=loc_clean.title(),
                reason="live_weather_feed_not_implemented",
            )

        info = KNOWN_CLIMATE.get(loc_clean.lower())
        if not info:
            return unavailable_result(
                "weather",
                location=loc_clean.title(),
                known_locations=sorted({k.title() for k in KNOWN_CLIMATE}),
                reason="unknown_location_no_live_feed",
            )

        return demo_result(
            "weather",
            mode="demo",
            location=loc_clean.title(),
            forecast_date=date_str,
            condition=info["condition"],
            temperature_range=info["temperature_range"],
            humidity=info["humidity"],
            precipitation_chance=info["precipitation_chance"],
            clothing_recommendation=info["clothing_recommendation"],
            notice=CLIMATE_NOTICE + " Labelled demo data.",
        )
