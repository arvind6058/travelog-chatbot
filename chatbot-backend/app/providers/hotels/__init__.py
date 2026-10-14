from typing import Dict, Any, List, Optional

from app.providers.availability import (
    demo_result,
    provider_mode,
    unavailable_result,
)

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

def _load_hotels_dataset() -> Dict[str, List[Dict[str, Any]]]:
    json_path = DATA_DIR / "hotels.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

SAMPLE_HOTELS: Dict[str, List[Dict[str, Any]]] = _load_hotels_dataset()


class HotelProvider:
    """
    Hotel provider adapter.
    Dispatches to live provider if configured, or falls back to static sample hotel data.
    """

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or provider_mode("hotels") or "mock").lower()

    @property
    def is_live(self) -> bool:
        return self.mode not in ("mock", "demo", "sample", "fake", "none", "unavailable", "")

    def search_hotels(self, location: str, max_price: Optional[int] = None, keyword: Optional[str] = None) -> Dict[str, Any]:
        loc_clean = (location or "").strip().lower()

        if self.is_live:
            # Live provider call logic here if implemented
            pass

        # Fallback to static sample dataset
        hotels = SAMPLE_HOTELS.get(loc_clean, [])
        if not hotels:
            # Check partial match
            for city_key, city_hotels in SAMPLE_HOTELS.items():
                if city_key in loc_clean or loc_clean in city_key:
                    hotels = city_hotels
                    break

        if max_price and hotels:
            hotels = [h for h in hotels if h.get("price_per_night", 0) <= max_price]

        if not hotels:
            return unavailable_result(
                "hotels",
                location=(location or "").strip().title(),
                max_price=max_price,
                hotels=[],
                count=0,
                reason="no_hotels_in_dataset",
            )

        return demo_result(
            "hotels",
            mode="demo",
            location=(location or "").strip().title(),
            city=(location or "").strip().title(),
            max_price=max_price,
            count=len(hotels),
            hotels=hotels,
            results=hotels,
        )

