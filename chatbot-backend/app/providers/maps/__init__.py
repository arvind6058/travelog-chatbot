import math
from typing import Dict, Any, Optional, Tuple

from app.providers.availability import calculated_result, provider_mode

# Reference coordinates (decimal degrees) used for a deterministic great-circle
# estimate. These are published city/landmark positions, not provider telemetry.
COORDINATES: Dict[str, Tuple[float, float]] = {
    "goa": (15.2993, 74.1240),
    "goa airport": (15.3808, 73.8314),
    "dabolim": (15.3808, 73.8314),
    "panaji": (15.4909, 73.8278),
    "baga beach": (15.5553, 73.7517),
    "baga": (15.5553, 73.7517),
    "calangute": (15.5439, 73.7553),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "new delhi": (28.6139, 77.2090),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "pune": (18.5204, 73.8567),
    "jaipur": (26.9124, 75.7873),
    "kochi": (9.9312, 76.2673),
    "manali": (32.2432, 77.1892),
    "shimla": (31.1048, 77.1734),
    "hampi": (15.3350, 76.4600),
    "coorg": (12.3375, 75.8069),
    "ooty": (11.4102, 76.6950),
    "munnar": (10.0889, 77.0595),
    "udaipur": (24.5854, 73.7125),
    "varanasi": (25.3176, 82.9739),
    "agra": (27.1767, 78.0081),
    "rishikesh": (30.0869, 78.2676),
    "darjeeling": (27.0360, 88.2627),
    "mysore": (12.2958, 76.6394),
    "mysuru": (12.2958, 76.6394),
    "mangalore": (12.9141, 74.8560),
    "hubli": (15.3647, 75.1240),
    "belgaum": (15.8497, 74.4977),
    "belagavi": (15.8497, 74.4977),
    "pondicherry": (11.9416, 79.8083),
    "puducherry": (11.9416, 79.8083),
    "madurai": (9.9252, 78.1198),
    "tirupati": (13.6288, 79.4192),
    "coimbatore": (11.0168, 76.9558),
    "calicut": (11.2588, 75.7804),
    "kozhikode": (11.2588, 75.7804),
    "trivandrum": (8.5241, 76.9366),
    "thiruvananthapuram": (8.5241, 76.9366),
    "gokarna": (14.5479, 74.3188),
    "wayanad": (11.6854, 76.1320),
    "chikkamagaluru": (13.3161, 75.7720),
    "chikmagalur": (13.3161, 75.7720),
}


class MapsProvider:
    """
    Maps provider adapter.

    No live routing service is wired up (MAPS_PROVIDER is a provider key without an
    adapter). This class therefore returns a *locally calculated* great-circle
    estimate and says so: it no longer reports an invented driving route name,
    which is what "via NH66 and Chogm Road" was for arbitrary city pairs.
    """

    CAB_RATE_INR_PER_KM = 18.0
    CAB_BASE_FARE_INR = 100.0

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or provider_mode("maps") or "calculated").lower()

    @staticmethod
    def _lookup(place: str) -> Optional[Tuple[float, float]]:
        key = (place or "").strip().lower()
        if key in COORDINATES:
            return COORDINATES[key]
        for name, coords in COORDINATES.items():
            if name in key or key in name:
                return coords
        return None

    @staticmethod
    def _haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        lat1, lon1 = math.radians(a[0]), math.radians(a[1])
        lat2, lon2 = math.radians(b[0]), math.radians(b[1])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 6371.0088 * 2 * math.asin(math.sqrt(h))

    def get_route(self, origin: str, destination: str, travel_mode: str = "driving") -> Dict[str, Any]:
        orig_clean = (origin or "").strip().title()
        dest_clean = (destination or "").strip().title()

        orig_coords = self._lookup(orig_clean)
        dest_coords = self._lookup(dest_clean)

        if not orig_coords or not dest_coords:
            return calculated_result(
                "maps",
                origin=orig_clean or None,
                destination=dest_clean or None,
                travel_mode=travel_mode,
                distance_km=None,
                duration_minutes=None,
                duration_formatted=None,
                recommended_route=None,
                cab_fare_estimate_inr=None,
                notice=(
                    "No reference coordinates are available for this pair, so no "
                    "distance can be calculated locally. Data unavailable from the "
                    "configured provider."
                ),
            )

        distance_km = round(self._haversine_km(orig_coords, dest_coords), 1)
        # Indicative road factor for Indian highways; explicitly an estimate.
        road_km = round(distance_km * 1.25, 1)
        duration_mins = max(1, int(round(road_km / 50 * 60)))

        hours, mins = divmod(duration_mins, 60)
        duration_str = f"{hours}h {mins}m" if hours else f"{mins} mins"

        return calculated_result(
            "maps",
            origin=orig_clean,
            destination=dest_clean,
            travel_mode=travel_mode,
            distance_km=distance_km,
            road_distance_estimate_km=road_km,
            duration_minutes=duration_mins,
            duration_formatted=duration_str,
            recommended_route=None,
            cab_fare_estimate_inr=round(road_km * self.CAB_RATE_INR_PER_KM + self.CAB_BASE_FARE_INR),
            notice=(
                "Locally calculated great-circle estimate from reference coordinates. "
                "Live routing is not configured."
            ),
        )
