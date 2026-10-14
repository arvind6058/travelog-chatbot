import re
import urllib.request
import urllib.error
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.core.config import get_settings
from app.core.logging import logger
from app.providers.flights.base import BaseFlightProvider
from app.providers.availability import unavailable_result

# Comprehensive City -> IATA Airport Code resolution table
CITY_TO_IATA: Dict[str, str] = {
    # Major Indian Metro Cities
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "blr": "BLR",
    "delhi": "DEL",
    "new delhi": "DEL",
    "del": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bom": "BOM",
    "chennai": "MAA",
    "madras": "MAA",
    "maa": "MAA",
    "hyderabad": "HYD",
    "hyd": "HYD",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "ccu": "CCU",
    "jaipur": "JAI",
    "jai": "JAI",
    "goa": "GOI",
    "goi": "GOI",
    "dabolim": "GOI",
    "mopa": "GOX",
    "gox": "GOX",
    "kochi": "COK",
    "cochin": "COK",
    "cok": "COK",
    "pune": "PNQ",
    "pnq": "PNQ",
    "ahmedabad": "AMD",
    "amd": "AMD",
    "chandigarh": "IXC",
    "ixc": "IXC",
    "lucknow": "LKO",
    "lko": "LKO",
    "thiruvananthapuram": "TRV",
    "trivandrum": "TRV",
    "trv": "TRV",
    "varanasi": "VNS",
    "vns": "VNS",
    "guwahati": "GAU",
    "gau": "GAU",
    "srinagar": "SXR",
    "sxr": "SXR",
    "amritsar": "ATQ",
    "atq": "ATQ",
    "coimbatore": "CJB",
    "cjb": "CJB",
    "bhubaneswar": "BBI",
    "bbi": "BBI",
    "indore": "IDR",
    "idr": "IDR",
    "patna": "PAT",
    "pat": "PAT",
    "visakhapatnam": "VTZ",
    "vtz": "VTZ",
    "surat": "STV",
    "stv": "STV",
    "mangalore": "IXE",
    "ixe": "IXE",
    "kozhikode": "CCJ",
    "calicut": "CCJ",
    "ccj": "CCJ",
    "tiruchirappalli": "TRZ",
    "trichy": "TRZ",
    "trz": "TRZ",
    "madurai": "IXM",
    "ixm": "IXM",
    "udaipur": "UDR",
    "udr": "UDR",
    # Major International Hubs
    "dubai": "DXB",
    "dxb": "DXB",
    "singapore": "SIN",
    "sin": "SIN",
    "london": "LHR",
    "lhr": "LHR",
    "new york": "JFK",
    "jfk": "JFK",
    "bangkok": "BKK",
    "bkk": "BKK",
    "doha": "DOH",
    "doh": "DOH",
    "abu dhabi": "AUH",
    "auh": "AUH",
    "kuala lumpur": "KUL",
    "kul": "KUL",
}


def resolve_iata_code(location: str) -> Optional[str]:
    """Convert city or location name to 3-letter IATA airport code."""
    if not location:
        return None
    cleaned = location.strip().lower()
    cleaned = re.sub(r"\b(?:airport|international|city)\b", "", cleaned).strip()
    
    if cleaned in CITY_TO_IATA:
        return CITY_TO_IATA[cleaned]
    
    # If already a 3-letter uppercase code
    if len(location.strip()) == 3 and location.strip().isalpha():
        return location.strip().upper()
        
    return None


class AviationstackFlightProvider(BaseFlightProvider):
    """
    Real Aviationstack Flight Provider integration.
    Connects to http://api.aviationstack.com/v1/flights using backend API key.
    """

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = (api_key or settings.AVIATIONSTACK_API_KEY or settings.FLIGHT_API_KEY or "").strip()
        self.base_url = "http://api.aviationstack.com/v1"

    def search_flights(self, origin: str, destination: str, travel_date: Optional[str] = None) -> Dict[str, Any]:
        dep_iata = resolve_iata_code(origin)
        arr_iata = resolve_iata_code(destination)

        if not self.api_key:
            logger.warning("Aviationstack search failed: AVIATIONSTACK_API_KEY is not configured.")
            return unavailable_result(
                "flights",
                source="aviationstack",
                mode="unavailable",
                is_mock=False,
                message="Current flight data is temporarily unavailable. Please try again.",
                notice="Current flight data is temporarily unavailable. Please try again.",
                origin=origin,
                destination=destination,
                travel_date=travel_date,
                reason="missing_api_key",
            )

        if not dep_iata or not arr_iata:
            logger.warning(f"Could not resolve IATA codes for origin='{origin}' ({dep_iata}), dest='{destination}' ({arr_iata})")
            return unavailable_result(
                "flights",
                source="aviationstack",
                mode="unavailable",
                is_mock=False,
                message="Current flight data is temporarily unavailable. Please try again.",
                notice="Could not resolve airport IATA code for requested route.",
                origin=origin,
                destination=destination,
                travel_date=travel_date,
                reason="unresolved_iata",
            )

        # Build Aviationstack API URL
        params = [
            f"access_key={self.api_key}",
            f"dep_iata={dep_iata}",
            f"arr_iata={arr_iata}",
            "limit=10",
        ]
        if travel_date and re.match(r"^\d{4}-\d{2}-\d{2}$", travel_date):
            params.append(f"flight_date={travel_date}")

        url = f"{self.base_url}/flights?{'&'.join(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TravelLogix-Backend/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_bytes = resp.read()
                data = json.loads(resp_bytes.decode("utf-8"))

            if "error" in data:
                err_info = data["error"]
                logger.error(f"Aviationstack API returned error: {err_info.get('code')} - {err_info.get('message')}")
                return unavailable_result(
                    "flights",
                    source="aviationstack",
                    mode="unavailable",
                    is_mock=False,
                    message="Current flight data is temporarily unavailable. Please try again.",
                    notice="Current flight data is temporarily unavailable. Please try again.",
                    origin=origin,
                    destination=destination,
                    travel_date=travel_date,
                    reason=err_info.get("code", "provider_error"),
                )

            raw_flights = data.get("data") or []
            parsed_flights: List[Dict[str, Any]] = []

            for item in raw_flights:
                flight_info = item.get("flight") or {}
                airline_info = item.get("airline") or {}
                dep_info = item.get("departure") or {}
                arr_info = item.get("arrival") or {}
                live_info = item.get("live") or {}

                fl_num = flight_info.get("iata") or flight_info.get("number") or "N/A"
                airline_name = airline_info.get("name") or "Unknown Airline"

                flight_obj = {
                    "flight_number": fl_num,
                    "airline": airline_name,
                    "airline_code": airline_info.get("iata"),
                    "flight_date": item.get("flight_date"),
                    "status": item.get("flight_status", "unknown"),
                    "departure": {
                        "airport": dep_info.get("airport"),
                        "iata": dep_info.get("iata"),
                        "scheduled": dep_info.get("scheduled"),
                        "estimated": dep_info.get("estimated"),
                        "actual": dep_info.get("actual"),
                        "terminal": dep_info.get("terminal"),
                        "gate": dep_info.get("gate"),
                        "delay_minutes": dep_info.get("delay"),
                    },
                    "arrival": {
                        "airport": arr_info.get("airport"),
                        "iata": arr_info.get("iata"),
                        "scheduled": arr_info.get("scheduled"),
                        "estimated": arr_info.get("estimated"),
                        "actual": arr_info.get("actual"),
                        "terminal": arr_info.get("terminal"),
                        "gate": arr_info.get("gate"),
                        "delay_minutes": arr_info.get("delay"),
                    },
                }

                if live_info and isinstance(live_info, dict) and live_info.get("latitude") is not None:
                    flight_obj["live_telemetry"] = {
                        "latitude": live_info.get("latitude"),
                        "longitude": live_info.get("longitude"),
                        "altitude": live_info.get("altitude"),
                        "speed": live_info.get("speed_horizontal"),
                        "direction": live_info.get("direction"),
                        "is_ground": live_info.get("is_ground"),
                        "updated": live_info.get("updated"),
                    }

                parsed_flights.append(flight_obj)

            return {
                "available": True,
                "found": len(parsed_flights) > 0,
                "provider": "aviationstack",
                "provider_mode": "aviationstack",
                "notice": "Live flight data from Aviationstack",
                "provenance": {
                    "source": "aviationstack",
                    "mode": "live",
                    "is_mock": False,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                },
                "origin": origin,
                "origin_code": dep_iata,
                "destination": destination,
                "destination_code": arr_iata,
                "travel_date": travel_date,
                "count": len(parsed_flights),
                "flights": parsed_flights,
            }

        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                pass
            logger.error(f"Aviationstack HTTP {e.code} error: {err_body[:300]}")
            return unavailable_result(
                "flights",
                source="aviationstack",
                mode="unavailable",
                is_mock=False,
                message="Current flight data is temporarily unavailable. Please try again.",
                notice="Current flight data is temporarily unavailable. Please try again.",
                origin=origin,
                destination=destination,
                travel_date=travel_date,
                reason=f"http_{e.code}",
            )
        except Exception as e:
            logger.error(f"Aviationstack request exception: {str(e)}")
            return unavailable_result(
                "flights",
                source="aviationstack",
                mode="unavailable",
                is_mock=False,
                message="Current flight data is temporarily unavailable. Please try again.",
                notice="Current flight data is temporarily unavailable. Please try again.",
                origin=origin,
                destination=destination,
                travel_date=travel_date,
                reason="connection_error",
            )

    def get_flight_status(self, flight_number: str) -> Dict[str, Any]:
        fl_num = (flight_number or "").upper().replace(" ", "").replace("_", "").replace("-", "")

        if not self.api_key:
            logger.warning("Aviationstack status check failed: AVIATIONSTACK_API_KEY is not configured.")
            return unavailable_result(
                "flights",
                source="aviationstack",
                mode="unavailable",
                is_mock=False,
                message="Current flight data is temporarily unavailable. Please try again.",
                flight_number=flight_number,
                reason="missing_api_key",
            )

        if not fl_num:
            return unavailable_result(
                "flights",
                source="aviationstack",
                mode="unavailable",
                is_mock=False,
                message="Please provide a valid flight number.",
                flight_number=flight_number,
                reason="invalid_flight_number",
            )

        url = f"{self.base_url}/flights?access_key={self.api_key}&flight_iata={fl_num}&limit=5"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TravelLogix-Backend/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if "error" in data:
                err_info = data["error"]
                logger.error(f"Aviationstack status API error: {err_info.get('code')} - {err_info.get('message')}")
                return unavailable_result(
                    "flights",
                    source="aviationstack",
                    mode="unavailable",
                    is_mock=False,
                    message="Current flight data is temporarily unavailable. Please try again.",
                    flight_number=flight_number,
                    reason=err_info.get("code", "provider_error"),
                )

            raw_flights = data.get("data") or []
            if not raw_flights:
                return {
                    "available": True,
                    "found": False,
                    "provider": "aviationstack",
                    "provider_mode": "aviationstack",
                    "flight_number": flight_number,
                    "message": f"No active flight record found for {flight_number}.",
                    "provenance": {
                        "source": "aviationstack",
                        "mode": "live",
                        "is_mock": False,
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    },
                }

            item = raw_flights[0]
            flight_info = item.get("flight") or {}
            airline_info = item.get("airline") or {}
            dep_info = item.get("departure") or {}
            arr_info = item.get("arrival") or {}
            live_info = item.get("live") or {}

            result = {
                "available": True,
                "found": True,
                "provider": "aviationstack",
                "provider_mode": "aviationstack",
                "provenance": {
                    "source": "aviationstack",
                    "mode": "live",
                    "is_mock": False,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                },
                "flight_number": flight_info.get("iata") or flight_number,
                "airline": airline_info.get("name"),
                "airline_code": airline_info.get("iata"),
                "status": item.get("flight_status"),
                "flight_date": item.get("flight_date"),
                "departure": {
                    "airport": dep_info.get("airport"),
                    "iata": dep_info.get("iata"),
                    "scheduled": dep_info.get("scheduled"),
                    "estimated": dep_info.get("estimated"),
                    "actual": dep_info.get("actual"),
                    "terminal": dep_info.get("terminal"),
                    "gate": dep_info.get("gate"),
                    "delay_minutes": dep_info.get("delay"),
                },
                "arrival": {
                    "airport": arr_info.get("airport"),
                    "iata": arr_info.get("iata"),
                    "scheduled": arr_info.get("scheduled"),
                    "estimated": arr_info.get("estimated"),
                    "actual": arr_info.get("actual"),
                    "terminal": arr_info.get("terminal"),
                    "gate": arr_info.get("gate"),
                    "delay_minutes": arr_info.get("delay"),
                },
            }

            if live_info and isinstance(live_info, dict) and live_info.get("latitude") is not None:
                result["live_telemetry"] = {
                    "latitude": live_info.get("latitude"),
                    "longitude": live_info.get("longitude"),
                    "altitude": live_info.get("altitude"),
                    "speed": live_info.get("speed_horizontal"),
                    "direction": live_info.get("direction"),
                    "is_ground": live_info.get("is_ground"),
                    "updated": live_info.get("updated"),
                }

            return result

        except Exception as e:
            logger.error(f"Aviationstack status request error: {str(e)}")
            return unavailable_result(
                "flights",
                source="aviationstack",
                mode="unavailable",
                is_mock=False,
                message="Current flight data is temporarily unavailable. Please try again.",
                flight_number=flight_number,
                reason="connection_error",
            )
