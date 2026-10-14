"""
Travelogix Knowledge Base Service (keyword retrieval, dependency-free).

Two scopes:

* ``scope="travel"``  - CUSTOMER travel chat. Returns only travel policies and a
  travel-services summary, and ONLY when the customer is actually asking about the
  platform or its policies. Ordinary travel questions ("plan 2 days in Hampi",
  "flights to Delhi") match nothing, so the answer comes from the LLM / providers,
  never from a platform brochure. Logistics content is never returned.
* ``scope="all"``     - original behaviour (travel + logistics + overview fallback)
  for the admin / logistics side.

Use ``query_travel_knowledge(q)`` from the customer chatbot.

Retrieval: tokenised, plural-folded keyword scoring. "buses" matches "bus",
"business" does not; the best-scoring topic wins; related topics are returned too.
"""
from __future__ import annotations

import copy
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

logger = logging.getLogger(__name__)

MAX_QUERY_CHARS = 1000
SCOPE_TRAVEL = "travel"
SCOPE_ALL = "all"

# NOTE: business statements below (refund %, delay compensation, support address)
# are carried over from the original file. Verify them before going live.
TRAVELOGIX_KNOWLEDGE_BASE: Dict[str, Any] = {
    "overview": {
        "title": "Travelogix — Integrated Travel & Logistics Platform",
        "description": (
            "Travelogix is an enterprise multi-agent platform unifying complete travel services "
            "(itineraries, flights, hotels, trains, buses, maps, and weather) with end-to-end "
            "logistics operations (shipment registration, milestone tracking, driver & vehicle "
            "administration, and verified telemetry monitoring)."
        ),
        "tagline": "Travel & Logistics in One Chat",
        "key_capabilities": [
            "AI-Assisted Multi-Day Travel Itinerary Generation & Budgeting",
            "Flight Search & Live Flight Status Tracking",
            "Hotel Search & Accommodation Recommendations",
            "Train Search & Indian Railways Live Running Status",
            "Intercity Bus Search & Live Bus Tracking",
            "Route Distance, Travel Duration & Cab Fare Estimates",
            "Weather Forecasts & Clothing Recommendations",
            "Freight Shipment Registration & Verified Milestone Tracking",
            "Real-Time Driver & Vehicle Telemetry Monitoring",
        ],
    },
    "travel_services": {
        "title": "Travelogix Travel Services",
        "details": [
            "Itinerary Generation: Customized multi-day trip plans with morning, afternoon, and evening activity breakdowns.",
            "Budget Planning: Cost estimates for intercity transport, stay, dining, local travel, and emergency reserves.",
            "Flight Services: Flight search and status lookups where a live flight provider is connected.",
            "Hotel Search: Filter hotels by location, price limit, star rating, and amenities (live rates only when a provider is connected).",
            "Train Services: Train searches, schedules and fares where a live provider is connected.",
            "Bus Services: Intercity bus options (Volvo, Sleeper, AC) where a live provider is connected.",
            "Route & Distance: Point-to-point distance, estimated travel duration, and cab fare estimates.",
            "Weather Forecasts: Current conditions, temperature, humidity, precipitation chances, and packing suggestions.",
        ],
    },
    "logistics_services": {
        "title": "Travelogix Logistics & Freight Services",
        "details": [
            "Shipment Registration: Book freight consignments specifying origin, destination, weight, package type, and recipient details.",
            "Real-Time Milestone Tracking: Track shipments with verified location updates, scanned event milestones, and delivery ETAs.",
            "Driver & Vehicle Management: Telemetry-verified driver assignments and vehicle registration tracking.",
            "Delivery Modes: Standard Road Freight, Express Air Freight, and Rail Cargo.",
        ],
    },
    "shipment_policies": {
        "title": "Travelogix Shipment & Service Policies",
        # "all" scope text (original wording, travel + freight)
        "cancellation_policy": (
            "Travel bookings (Flights/Hotels/Trains) cancelled more than 24 hours prior to departure "
            "receive an 85%-100% refund depending on carrier terms. Freight bookings cancelled prior to pickup "
            "receive a full refund minus a nominal processing fee."
        ),
        "packaging_rules": (
            "Fragile items require double-walled corrugated boxing and bubble-wrap insulation. "
            "Hazardous materials (flammables, explosives, toxic chemicals, and unauthorized items) are strictly prohibited."
        ),
        "delay_policy": (
            "For carrier delays exceeding 3 hours, Travelogix provides complimentary trip re-routing and hotel stay credits. "
            "For freight shipments, real-time telemetry updates keep senders and recipients notified of adjusted ETAs."
        ),
        "support_contacts": "24/7 customer support is available via support@travelogix.internal.",
    },
    # Travel-only wording used by scope="travel" (no freight content).
    "travel_policies": {
        "title": "Travelogix Travel Policies",
        "cancellation_policy": (
            "Travel bookings (flights, hotels, trains) cancelled more than 24 hours before departure "
            "receive an 85%-100% refund depending on carrier terms."
        ),
        "delay_policy": (
            "For carrier delays exceeding 3 hours, Travelogix provides complimentary trip re-routing and hotel stay credits."
        ),
        "support_contacts": "24/7 customer support is available via support@travelogix.internal.",
    },
}

# --------------------------------------------------------------------------- #
# Retrieval configuration
# --------------------------------------------------------------------------- #
# Ambiguous words that caused false matches were removed: "help" ("help me plan a
# trip" returned the support address), "customer", "late", "box"/"boxing", "credit", "eta".
_POLICY_SECTION_KEYWORDS: Dict[str, FrozenSet[str]] = {
    "cancellation_policy": frozenset(
        {"cancel", "cancellation", "cancelled", "cancelling", "refund", "refunded", "reimbursement"}
    ),
    "packaging_rules": frozenset({"packaging", "fragile", "hazardous", "prohibited", "restricted", "bubble"}),
    "delay_policy": frozenset({"delay", "delayed", "reroute", "rerouting", "compensation"}),
    "support_contacts": frozenset({"support", "contact", "email", "helpline"}),
}
_GENERIC_POLICY_WORDS: FrozenSet[str] = frozenset({"policy", "rule", "term", "condition", "guideline"})

# scope="all": original topic routing (priority order = tie-break order).
_TOPIC_KEYWORDS_ALL: Dict[str, FrozenSet[str]] = {
    "shipment_and_service_policies": _GENERIC_POLICY_WORDS.union(*_POLICY_SECTION_KEYWORDS.values()),
    "logistics_services": frozenset({
        "logistics", "freight", "shipment", "parcel", "courier", "package", "consignment",
        "cargo", "driver", "vehicle", "telemetry", "milestone", "delivery", "pickup",
    }),
    "travel_services": frozenset({
        "travel", "flight", "hotel", "train", "bus", "itinerary", "trip", "weather",
        "route", "cab", "railway", "stay", "budget", "distance",
    }),
}

# scope="travel": the KB answers only platform/policy questions, never general travel ones.
_TRAVEL_POLICY_SECTIONS = ("cancellation_policy", "delay_policy", "support_contacts")
_PLATFORM_WORDS: FrozenSet[str] = frozenset({"travelogix", "service", "feature", "capability", "offer", "platform"})
_TOPIC_KEYWORDS_TRAVEL: Dict[str, FrozenSet[str]] = {
    "travel_policies": _GENERIC_POLICY_WORDS.union(*(_POLICY_SECTION_KEYWORDS[k] for k in _TRAVEL_POLICY_SECTIONS)),
    "travel_services": _PLATFORM_WORDS,
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _normalise(token: str) -> str:
    """Light plural folding: policies->policy, buses->bus, flights->flight, business stays."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("ses"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _tokenise(text: str) -> FrozenSet[str]:
    return frozenset(_normalise(t) for t in _TOKEN_RE.findall(text.lower()))


def _score_topics(tokens: FrozenSet[str], topics: Dict[str, FrozenSet[str]]) -> List[Tuple[str, int, List[str]]]:
    """[(topic, score, matched_terms)] for topics with >=1 hit, best first (stable on ties)."""
    scored = []
    for topic, keywords in topics.items():
        hits = sorted(tokens & keywords)
        if hits:
            scored.append((topic, len(hits), hits))
    return sorted(scored, key=lambda item: -item[1])


# --------------------------------------------------------------------------- #
# Payload builders (always deep-copied)
# --------------------------------------------------------------------------- #
def _build_policies(tokens: FrozenSet[str]) -> Dict[str, Any]:
    policies = TRAVELOGIX_KNOWLEDGE_BASE["shipment_policies"]
    wanted = [key for key, kws in _POLICY_SECTION_KEYWORDS.items() if tokens & kws]
    sections = wanted or list(_POLICY_SECTION_KEYWORDS)
    payload: Dict[str, Any] = {"topic": "shipment_and_service_policies", "title": policies["title"]}
    payload.update({key: policies[key] for key in sections})
    return payload


def _build_travel_policies(tokens: FrozenSet[str]) -> Dict[str, Any]:
    policies = TRAVELOGIX_KNOWLEDGE_BASE["travel_policies"]
    wanted = [k for k in _TRAVEL_POLICY_SECTIONS if tokens & _POLICY_SECTION_KEYWORDS[k]]
    sections = wanted or list(_TRAVEL_POLICY_SECTIONS)  # generic "policy" -> all travel sections
    payload: Dict[str, Any] = {"topic": "travel_policies", "title": policies["title"]}
    payload.update({key: policies[key] for key in sections})
    return payload


def _build_logistics() -> Dict[str, Any]:
    kb = TRAVELOGIX_KNOWLEDGE_BASE
    return {
        "topic": "logistics_services",
        "title": kb["logistics_services"]["title"],
        "services": kb["logistics_services"]["details"],
        "platform_overview": kb["overview"]["description"],
    }


def _build_travel() -> Dict[str, Any]:
    kb = TRAVELOGIX_KNOWLEDGE_BASE
    return {
        "topic": "travel_services",
        "title": kb["travel_services"]["title"],
        "services": kb["travel_services"]["details"],
        "platform_overview": kb["overview"]["description"],
    }


def _build_travel_only() -> Dict[str, Any]:
    """Travel services summary for the customer chat: no logistics, no platform pitch."""
    kb = TRAVELOGIX_KNOWLEDGE_BASE
    return {
        "topic": "travel_services",
        "title": kb["travel_services"]["title"],
        "travel_services": kb["travel_services"]["details"],
    }


def _build_overview() -> Dict[str, Any]:
    kb = TRAVELOGIX_KNOWLEDGE_BASE
    return {
        "topic": "platform_overview",
        "title": kb["overview"]["title"],
        "description": kb["overview"]["description"],
        "tagline": kb["overview"]["tagline"],
        "key_capabilities": kb["overview"]["key_capabilities"],
        "travel_services": kb["travel_services"]["details"],
        "logistics_services": kb["logistics_services"]["details"],
        "policies": {k: v for k, v in kb["shipment_policies"].items() if k != "title"},
    }


def _build_topic(topic: str, tokens: FrozenSet[str], scope: str) -> Dict[str, Any]:
    if topic == "shipment_and_service_policies":
        data = _build_policies(tokens)
    elif topic == "travel_policies":
        data = _build_travel_policies(tokens)
    elif topic == "logistics_services":
        data = _build_logistics()
    elif topic == "travel_services":
        data = _build_travel_only() if scope == SCOPE_TRAVEL else _build_travel()
    else:
        data = _build_overview()
    return copy.deepcopy(data)


def _provenance(retrieval: str, scope: str) -> Dict[str, Any]:
    return {
        "source": "travelogix_knowledge_base",
        "mode": "rag",
        "retrieval": retrieval,  # keyword_match | fallback_overview | no_match | none
        "scope": scope,
        "is_mock": False,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def query_knowledge_base(query: str, scope: str = SCOPE_ALL) -> Dict[str, Any]:
    """
    Query the knowledge base.

    Returns:
      * ``success``            - False only for an invalid query;
      * ``knowledge_data``     - best-matching topic, or ``None`` when nothing matched
                                 in ``scope="travel"`` (answer from the LLM instead);
      * ``matched_terms``      - query words that triggered the match;
      * ``additional_topics``  - other topics the query also touched, best first;
      * ``provenance``         - source, scope, retrieval mode and timestamp.

    ``scope="all"`` (default) keeps the original behaviour, including the overview
    fallback when nothing matches. ``scope="travel"`` never returns logistics content
    or the platform overview.
    """
    scope = SCOPE_TRAVEL if str(scope).lower() == SCOPE_TRAVEL else SCOPE_ALL

    if not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "query": query if isinstance(query, str) else None,
            "error": "Query must be a non-empty string.",
            "provenance": _provenance("none", scope),
        }

    query = query.strip()[:MAX_QUERY_CHARS]
    tokens = _tokenise(query)
    topics = _TOPIC_KEYWORDS_TRAVEL if scope == SCOPE_TRAVEL else _TOPIC_KEYWORDS_ALL
    ranked = _score_topics(tokens, topics)

    data: Optional[Dict[str, Any]]
    if ranked:
        primary_topic, _, matched = ranked[0]
        data = _build_topic(primary_topic, tokens, scope)
        additional = [_build_topic(topic, tokens, scope) for topic, _, _ in ranked[1:]]
        retrieval = "keyword_match"
    elif scope == SCOPE_TRAVEL:
        # Not a platform/policy question: do NOT pad with the brochure.
        data, additional, matched, retrieval = None, [], [], "no_match"
    else:
        data = _build_topic("platform_overview", tokens, scope)
        additional, matched, retrieval = [], [], "fallback_overview"

    logger.debug("KB query=%r scope=%s topic=%s matched=%s", query, scope, data and data["topic"], matched)

    return {
        "success": True,
        "query": query,
        "knowledge_data": data,
        "matched_terms": matched,
        "additional_topics": additional,
        "provenance": _provenance(retrieval, scope),
    }


def query_travel_knowledge(query: str) -> Dict[str, Any]:
    """Customer travel-chat entry point (travel-only scope)."""
    return query_knowledge_base(query, scope=SCOPE_TRAVEL)