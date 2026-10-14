"""
Shared provider-mode helpers.

A provider setting of "mock" means there is NO live backend behind that provider.
The README (section 7) promises that when provider data is unavailable the system
outputs exactly `Data unavailable from the configured provider` instead of
inventing telemetry (gates, ETAs, GPS coordinates, seat counts, forecasts).
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.config import get_settings

UNAVAILABLE_MESSAGE = "Data unavailable from the configured provider"

# Settings flag per provider domain.
PROVIDER_SETTINGS: Dict[str, str] = {
    "flights": "FLIGHT_PROVIDER",
    "trains": "TRAIN_PROVIDER",
    "buses": "BUS_PROVIDER",
    "hotels": "HOTEL_PROVIDER",
    "maps": "MAPS_PROVIDER",
    "weather": "WEATHER_PROVIDER",
    "courier": "COURIER_PROVIDER",
}

# Modes that mean "there is no live upstream for this data".
NON_LIVE_MODES = {"mock", "demo", "sample", "fake", "none", "unavailable", ""}


def provider_mode(domain: str) -> str:
    """Configured mode string for a provider domain (never raises)."""
    try:
        settings = get_settings()
        attr = PROVIDER_SETTINGS.get(domain, "")
        value = getattr(settings, attr, "") if attr else ""
        return (value or "").strip().lower()
    except Exception:
        return "mock"


def is_live_provider(domain: str) -> bool:
    """True only when a real (non-mock) upstream is configured for this domain."""
    return provider_mode(domain) not in NON_LIVE_MODES


def unavailable_result(domain: str, **extra: Any) -> Dict[str, Any]:
    """
    Explicit "we cannot serve this" payload.

    `is_mock` is False because nothing was fabricated; `mode` is "unavailable" and
    the customer-facing message is the README literal.
    """
    payload: Dict[str, Any] = {
        "available": False,
        "found": False,
        "provider": domain,
        "provider_mode": provider_mode(domain) or "unconfigured",
        "message": UNAVAILABLE_MESSAGE,
        "notice": UNAVAILABLE_MESSAGE,
        "provenance": {
            "source": f"{domain}_provider_unavailable",
            "mode": "unavailable",
            "is_mock": False,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    payload.update(extra)
    return payload


def demo_result(domain: str, mode: str = "demo", **extra: Any) -> Dict[str, Any]:
    """
    Demo/sample payload. Anything returned through this helper is labelled as
    demo both structurally and in the customer-facing text.
    """
    payload: Dict[str, Any] = {
        "available": True,
        "demo_label": "DEMO DATA",
        "notice": (
            "Sample data from the configured demo provider "
            "(no live upstream is configured)."
        ),
        "provenance": {
            "source": f"{domain}_demo_provider",
            "mode": mode if mode in ("demo", "sample") else "demo",
            "is_mock": True,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    payload.update(extra)
    return payload


def calculated_result(domain: str, **extra: Any) -> Dict[str, Any]:
    """Locally computed/derived payload: honest, deterministic, not 'live'."""
    payload: Dict[str, Any] = {
        "available": True,
        "notice": "Locally calculated estimate - not live provider data.",
        "provenance": {
            "source": f"{domain}_calculator",
            "mode": "calculated",
            "is_mock": False,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    payload.update(extra)
    return payload


def is_unavailable(result: Optional[Dict[str, Any]]) -> bool:
    """True when a tool/provider result carries the unavailable literal."""
    if not isinstance(result, dict):
        return False
    if result.get("available") is False:
        return True
    provenance = result.get("provenance") or {}
    return provenance.get("mode") == "unavailable" or result.get("message") == UNAVAILABLE_MESSAGE
