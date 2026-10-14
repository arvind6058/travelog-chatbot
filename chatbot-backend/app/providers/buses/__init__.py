from typing import Dict, Any, List, Optional

from app.providers.availability import (
    demo_result,
    is_live_provider,
    provider_mode,
    unavailable_result,
)

import json
from pathlib import Path
from typing import Tuple

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

def _load_buses_dataset() -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Dict[str, Any]]]:
    json_path = DATA_DIR / "buses.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("buses", {}), data.get("statuses", {})
        except Exception:
            pass
    return {}, {}

SAMPLE_BUSES, SAMPLE_BUS_STATUS = _load_buses_dataset()


class BusProvider:
    """
    Bus provider adapter for intercity bus search and running status.
    Dispatches to live provider if configured, or falls back to static sample bus dataset.
    """

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or provider_mode("buses") or "demo").lower()

    @property
    def is_live(self) -> bool:
        return self.mode not in ("mock", "demo", "sample", "fake", "none", "unavailable", "")

    def search_buses(self, origin: str, destination: str, bus_type: Optional[str] = None) -> Dict[str, Any]:
        orig_clean = (origin or "").strip().lower()
        dest_clean = (destination or "").strip().lower()
        route_key = f"{orig_clean}-{dest_clean}"
        rev_route_key = f"{dest_clean}-{orig_clean}"

        if self.is_live:
            pass

        buses = SAMPLE_BUSES.get(route_key) or SAMPLE_BUSES.get(rev_route_key) or []

        if not buses:
            for k, b_list in SAMPLE_BUSES.items():
                if orig_clean in k and dest_clean in k:
                    buses = b_list
                    break

        if not buses:
            return unavailable_result(
                "buses",
                origin=(origin or "").title(),
                destination=(destination or "").title(),
                buses=[],
                count=0,
                reason="no_buses_in_dataset",
            )

        return demo_result(
            "buses",
            mode="demo",
            origin=(origin or "").title(),
            destination=(destination or "").title(),
            count=len(buses),
            buses=buses,
            results=buses,
        )

    def get_bus_status(self, bus_id_or_operator: str) -> Dict[str, Any]:
        id_clean = (bus_id_or_operator or "").strip().upper()

        if self.is_live:
            pass

        st = None
        for k, val in SAMPLE_BUS_STATUS.items():
            key = k.upper()
            if key in id_clean or id_clean in key:
                st = val
                break
            if val.get("operator", "").upper() in id_clean or id_clean in val.get("operator", "").upper():
                st = val
                break

        if not st:
            # Unknown service: never invent a position. Previously this answered
            # "Intercity Express / Highway Waypoint / Running On Time" for anything.
            return unavailable_result(
                "buses",
                bus_identifier=id_clean or None,
                reason="no_running_status_in_dataset",
            )

        return demo_result(
            "buses",
            mode="demo",
            bus_identifier=st.get("bus_identifier", id_clean),
            operator=st.get("operator"),
            route=st.get("route"),
            current_location=st.get("current_location"),
            status=st.get("status"),
            delay_minutes=st.get("delay_minutes", 0),
            eta=st.get("eta"),
        )

