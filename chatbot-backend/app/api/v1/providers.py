from typing import Dict, Any, Optional
from fastapi import APIRouter, Body
from pydantic import BaseModel
from app.core.config import get_settings
from app.providers.flights import FlightProvider

router = APIRouter(tags=["Providers & Travel Services"])

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    date: Optional[str] = None

@router.get("/providers/status", summary="Provider configuration diagnostic status")
async def get_providers_status() -> Dict[str, Any]:
    settings = get_settings()
    provider_name = (settings.FLIGHT_PROVIDER or "aviationstack").lower()
    has_key = bool((settings.AVIATIONSTACK_API_KEY or settings.FLIGHT_API_KEY or "").strip())
    
    return {
        "flights": {
            "provider": provider_name,
            "configured": has_key,
            "available": has_key and provider_name != "unavailable",
        }
    }

@router.post("/travel/flights/search", summary="Direct flight search endpoint for testing/backend service")
async def search_flights_endpoint(req: FlightSearchRequest = Body(...)) -> Dict[str, Any]:
    provider = FlightProvider()
    return provider.search_flights(
        origin=req.origin,
        destination=req.destination,
        travel_date=req.date
    )
