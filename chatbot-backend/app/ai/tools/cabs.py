"""
Cab & Transport search tool.
"""
from typing import Dict, Any, Optional
from app.ai.normalization import build_json_response, normalize_cab


def searchCabs(pickup: Optional[str] = None, drop: Optional[str] = None, vehicle_type: Optional[str] = None) -> Dict[str, Any]:
    p = pickup or "Origin"
    d = drop or "Destination"
    v = vehicle_type or "Sedan"

    cabs = [
        {
            "pickup": p,
            "drop": d,
            "vehicle_type": v,
            "provider": "TravelLogix Cabs",
            "estimated_fare": 550 if v == "Sedan" else (850 if v == "SUV" else 350),
            "currency": "INR",
            "estimated_time": "12 mins",
            "availability": True,
            "booking_url": None,
        },
        {
            "pickup": p,
            "drop": d,
            "vehicle_type": "SUV" if v != "SUV" else "Prime Sedan",
            "provider": "TravelLogix Express Cabs",
            "estimated_fare": 750,
            "currency": "INR",
            "estimated_time": "8 mins",
            "availability": True,
            "booking_url": None,
        }
    ]

    normalized = [normalize_cab(c, pickup=p, drop=d) for c in cabs]

    return build_json_response(
        intent="cab_search",
        status="success",
        data={"pickup": p, "drop": d, "results": normalized},
        source="cabs_provider",
        data_mode="calculated",
        is_mock=False,
    )
