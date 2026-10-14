from typing import Dict, Any, List, Optional

from app.providers.availability import (
    demo_result,
    is_live_provider,
    provider_mode,
    unavailable_result,
)

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

def _load_trains_dataset() -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Dict[str, Any]]]:
    json_path = DATA_DIR / "trains.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("trains", {}), data.get("statuses", {})
        except Exception:
            pass
    return {}, {}

from typing import Tuple
SAMPLE_TRAINS, SAMPLE_TRAIN_STATUS = _load_trains_dataset()


class TrainProvider:
    """
    Train provider adapter for searching Indian Railways trains and running status.
    Dispatches to live provider if configured, or falls back to static sample train dataset.
    """

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or provider_mode("trains") or "demo").lower()

    @property
    def is_live(self) -> bool:
        return self.mode not in ("mock", "demo", "sample", "fake", "none", "unavailable", "")

    def search_trains(self, origin: str, destination: str) -> Dict[str, Any]:
        orig_clean = (origin or "").strip().lower()
        dest_clean = (destination or "").strip().lower()
        route_key = f"{orig_clean}-{dest_clean}"
        rev_route_key = f"{dest_clean}-{orig_clean}"

        if self.is_live:
            pass

        trains = SAMPLE_TRAINS.get(route_key) or SAMPLE_TRAINS.get(rev_route_key) or []

        if not trains:
            # Match by city names in key
            for k, tr_list in SAMPLE_TRAINS.items():
                if orig_clean in k and dest_clean in k:
                    trains = tr_list
                    break

        if not trains:
            return unavailable_result(
                "trains",
                origin=(origin or "").title(),
                destination=(destination or "").title(),
                trains=[],
                count=0,
                reason="no_trains_found_in_dataset",
            )

        return demo_result(
            "trains",
            mode="demo",
            origin=(origin or "").title(),
            destination=(destination or "").title(),
            count=len(trains),
            trains=trains,
            results=trains,
        )

    def get_train_status(self, train_number_or_name: str) -> Dict[str, Any]:
        num_clean = (train_number_or_name or "").strip().upper()

        if self.is_live:
            pass

        st = SAMPLE_TRAIN_STATUS.get(num_clean)
        if not st:
            for k, val in SAMPLE_TRAIN_STATUS.items():
                if k in num_clean or num_clean in val.get("train_name", "").upper():
                    st = val
                    break

        if not st:
            # Unknown train: never invent a running status. Previously this returned
            # "Express Train / Running On Time / Main Junction", which read like a
            # verified live position for a train that does not exist in the dataset.
            return unavailable_result(
                "trains",
                train_number=num_clean or None,
                reason="no_running_status_in_dataset",
            )

        return demo_result(
            "trains",
            mode="demo",
            train_number=st.get("train_number", num_clean),
            train_name=st.get("train_name"),
            status=st.get("status"),
            current_station=st.get("current_station"),
            last_passed_station=st.get("last_passed_station"),
            next_station=st.get("next_station"),
            delay_minutes=st.get("delay_minutes", 0),
        )

