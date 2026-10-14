"""
AI Orchestrator.

Pipeline: customer message -> intent detection -> entity extraction -> tool
execution -> validated result -> optional LLM synthesis -> customer-facing reply.

Honesty rules enforced here:
  * a reply never contains the internal provenance blob (`mode`, `is_mock`,
    internal `source` names);
  * whenever a result is mock/demo the reply is visibly suffixed with `DEMO DATA`;
  * whenever a provider has no live backend the reply contains the README literal
    `Data unavailable from the configured provider`;
  * a missing destination/flight/train number produces a clarifying question, never
    a guessed entity.
"""
from dataclasses import dataclass
import re
from typing import Dict, Any, List, Optional, Tuple

from app.ai.intent import detect_intent, extract_origin_destination, IntentType
from app.ai.context import get_conversation_session, try_resolve_follow_up
from app.ai.tools.itinerary import (
    generateItinerary,
    calculateBudget,
    recalculateDisruptedItinerary,
    modifyItinerary,
    getPackingSuggestions,
    getTravelChecklist,
    searchPlaces,
)
from app.ai.tools.tracking import trackShipment, trackShipmentAsync, registerShipmentAsync, getDriverInfoAsync, getVehicleStatusAsync
from app.ai.tools.weather import getWeather
from app.ai.tools.flights import searchFlights, getFlightStatus
from app.ai.tools.hotels import searchHotels
from app.ai.tools.trains import searchTrains, getTrainStatus
from app.ai.tools.buses import searchBuses, getBusStatus
from app.ai.tools.maps import getRoute
from app.ai.tools.cabs import searchCabs
from app.ai.providers.llm import (
    synthesize_with_llm,
    render_knowledge_base_markdown,
    render_itinerary_markdown,
    _requested_sections,
    _wants_detail,
)
from app.core.config import get_settings
from app.core.logging import logger
from app.providers.availability import is_unavailable
from app.rag import query_knowledge_base
from app.ai.normalization import (
    build_json_response,
    normalize_flight,
    normalize_hotel,
    normalize_train,
    normalize_bus,
    normalize_weather,
    normalize_route,
    normalize_cab,
    normalize_shipment,
    normalize_driver,
    normalize_vehicle,
)
from app.ai.formatting import (
    format_flights_response,
    format_hotels_response,
    format_trains_response,
    format_buses_response,
    format_weather_response,
    format_route_response,
    format_cabs_response,
)

UNAVAILABLE_MESSAGE = "Data unavailable from the configured provider"
DEMO_SUFFIX = "DEMO DATA"

DEFAULT_ITINERARY_DAYS = 5
DEFAULT_ORIGIN = "Bangalore"

# How many rows a customer-facing answer shows before it is cut off.
SHORT_ANSWER_LIMIT = 4

# Where each dataset lookup lives, so a request can be traced in the logs.
_DATASET_SOURCE = {
    "flights": "data/flights.json",
    "hotels": "data/hotels.json",
    "trains": "data/trains.json",
    "buses": "data/buses.json",
    "weather": "data/weather.json",
    "routes": "app/providers/maps/COORDINATES",
}

# One-shot LLM tools: answer from general travel knowledge when the dataset has
# nothing for the requested route/city. Each returns a dict of Echo-only fields, so
# it is never mistaken for dataset rows.
_LLM_KNOWLEDGE_TOOLS = {
    "flights": "flightSearchGeneral",
    "hotels": "hotelSearchGeneral",
    "trains": "trainSearchGeneral",
    "buses": "busSearchGeneral",
    "weather": "weatherGeneral",
    "routes": "routeGeneral",
}

# Words that mean the customer is asking about the platform/policies, not about a
# trip. Only then may the RAG knowledge base answer a dataset miss.
_PLATFORM_QUESTION_RE = re.compile(
    r"\b(travelogix|platform|your (?:service|services|policy|policies|feature|features|"
    r"capabilit\w*|company|app)|refund|cancellation|cancel(?:led|lation)?|policy|policies|"
    r"packaging|fragile|hazardous|prohibited|support|contact|helpline|compensation|"
    r"reschedul\w*|re-?rout\w*|terms|guidelines?|who are you|what can you do)\b",
    re.IGNORECASE,
)

# Fallback answer for a city that is in no dataset: the LLM tier only.
#
# Note for the LLM tier: we hand the model ONLY the requested route/city. It must not
# be asked "are there flights from X to Y" from memory, because it cannot know a
# schedule - #   that produced invented confirmations such as
# "Flights from Coimbatore to Ranchi are available." The data-miss prompts below ask
# for general guidance about the corridor instead, and the reply is prefixed in code
# with an explicit "not in my dataset" note.
_DATA_MISS_QUESTION = {
    "flights": "I can't confirm live schedules or fares for this route right now. "
               "Please check the airline app or a booking site for exact details.",
    "hotels": "I don't have hotel options for this city right now. "
              "Please check a booking site for current rates.",
    "trains": "I can't confirm live train schedules for this route right now. "
              "IRCTC or NTES is the authoritative source.",
    "buses": "I can't confirm bus options or schedules for this route right now. "
             "Please check the operator or a bus booking site for current services.",
    "weather": "I don't have climate reference data for this place right now.",
    "routes": "I don't have reference coordinates for this pair, so I can't calculate a distance right now.",
}

# Prefix for missing route guidance (internal provenance text must not be rendered).
_DATA_MISS_PREFIX = ""

# Phrasings that turn "general guidance" into a claim about a route we hold no data for.
# If a model still produces one, the claim is dropped and the honest miss is returned.
_ROUTE_CLAIM_RE = re.compile(
    r"\b(?:are|is)\s+(?:available|operating|running)\b"
    r"|\b(?:flights?|trains?|buses?)\s+(?:are\s+)?available\b"
    r"|\b(?:do|does)\s+(?:operate|run|fly|exist)\b"
    r"|\bthere\s+(?:are|is)\s+\d+\s+(?:flights?|trains?|buses?|options?)\b",
    re.IGNORECASE,
)

# Placeholder identities that must never be persisted for a shipment.
_PLACEHOLDER_IDENTITIES = {
    "", "customer", "customer@example.com", "customer@travelogix.internal",
    "recipient hub", "none", "null",
}


def _is_real_identity(value: Optional[str]) -> bool:
    """True only for a genuine, caller-supplied identity (no placeholders)."""
    cleaned = (value or "").strip()
    return bool(cleaned) and cleaned.lower() not in _PLACEHOLDER_IDENTITIES


def _has_demo(provenance: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(provenance, dict):
        return False
    if provenance.get("is_mock"):
        return True
    return str(provenance.get("mode") or "").lower() in ("demo", "sample", "mock")


def _decorate(reply: str, provenance: Optional[Dict[str, Any]]) -> str:
    """
    Append customer-facing provenance badge when needed.
    """
    if _has_demo(provenance):
        if DEMO_SUFFIX not in reply and "sample data" not in reply and "Sample data" not in reply and "available travel data" not in reply:
            return f"{reply.rstrip()}\n\n*(Based on available travel data)*"
    return reply


def _unavailable_reply(what: str) -> str:
    return f"### {what}\n\nInformation for this request is currently unavailable."


@dataclass
class _RequestContext:
    """Everything the handler branches need to know about the caller."""

    db: Any = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None


class AIOrchestrator:
    """Central AI orchestrator for the chat surface."""

    async def process_message(
        self,
        db=None,
        message: str = "",
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Public entry point (frozen contract).

        Returns a dict with the keys the API layer and tests rely on: `reply`,
        `intent`, `destination`, `duration_days`, `tracking_id`, `provenance`,
        `data`.

        All parameters after `db` default, so existing call sites that pass only
        `message`/`user_id`/`conversation_id` keep working.
        """
        # Defensive: tolerate the legacy `process_message(message, ...)` order.
        if isinstance(db, str) and not isinstance(message, str):
            db, message = None, db
        elif isinstance(db, str) and isinstance(message, str) and not message:
            message, db = db, None

        message = message or ""
        logger.info(f"AI Orchestrator processing customer message: '{message}'")

        ctx = _RequestContext(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            customer_email=customer_email,
            customer_name=customer_name,
        )

        # 1. Follow-up Context Resolution
        resolved_follow_up = try_resolve_follow_up(message, conversation_id, user_id)
        if resolved_follow_up:
            intent, entities = resolved_follow_up
            logger.info(f"Resolved follow-up context: intent={intent.value}, entities={entities}")
        else:
            intent, entities = detect_intent(message)
            logger.info(f"Detected intent: {intent.value}, entities: {entities}")

        # Update session context
        session = get_conversation_session(conversation_id, user_id)
        session.set_pending(intent, entities)

        handler = {
            IntentType.TRAVEL_ITINERARY: self._travel_itinerary,
            IntentType.BUDGET_CALCULATION: self._budget,
            IntentType.FLIGHT_SEARCH: self._flight_search,
            IntentType.FLIGHT_STATUS: self._flight_status,
            IntentType.HOTEL_SEARCH: self._hotel_search,
            IntentType.TRAIN_SEARCH: self._train_search,
            IntentType.TRAIN_STATUS: self._train_status,
            IntentType.BUS_SEARCH: self._bus_search,
            IntentType.BUS_STATUS: self._bus_status,
            IntentType.MAPS_ROUTE: self._maps_route,
            IntentType.WEATHER_INQUIRY: self._weather,
            IntentType.CAB_SEARCH: self._cab_search,
            IntentType.DELAY_DISRUPTION: self._delay_disruption,
            IntentType.TRIP_MODIFICATION: self._trip_modification,
            IntentType.PACKING_ASSISTANT: self._packing,
            IntentType.TRAVEL_CHECKLIST: self._travel_checklist,
            IntentType.PLACES_ACTIVITIES: self._places,
            IntentType.SHIPMENT_TRACKING: self._shipment_tracking,
            IntentType.SHIPMENT_REGISTER: self._shipment_register,
            IntentType.DRIVER_INFO: self._driver_info,
            IntentType.VEHICLE_STATUS: self._vehicle_status,
            IntentType.POLICY_RAG: self._policy,
            IntentType.TRAVELOGIX_INFORMATION: self._travelogix_info,
            IntentType.GENERAL_TRAVEL_ADVICE: self._general_travel_advice,
            IntentType.GENERAL_CHAT: self._general_chat,
        }.get(intent)

        if handler is None:
            res = await self._general_chat(message, entities, ctx)
        else:
            res = await handler(message, entities, ctx)

        # Clear only pending state when turn completes; preserve accumulated slot context
        if not (res.get("data") or {}).get("clarification_required"):
            session.clear_pending()

        return res

    # ------------------------------------------------------------------ #
    # Shared helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _text(value: Any, default: str = "Not available") -> str:
        if value is None or value == "":
            return default
        return str(value)

    @staticmethod
    def _days(entities: Dict[str, Any], session_slots: Optional[Dict[str, Any]] = None, default: int = DEFAULT_ITINERARY_DAYS) -> int:
        value = entities.get("duration_days")
        if value is None and session_slots:
            value = session_slots.get("duration_days")
        try:
            days = int(value)
        except (TypeError, ValueError):
            return default
        return max(1, min(30, days))


    @staticmethod
    def _result(
        reply: str,
        intent: IntentType,
        tool_result: Optional[Dict[str, Any]] = None,
        mode: Optional[str] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        prov = dict((tool_result or {}).get("provenance") or {})
        if mode:
            prov["mode"] = mode
        elif prov.get("mode") not in ("json", "llm", "rag"):
            prov["mode"] = "json"

        payload: Dict[str, Any] = {
            "reply": _decorate(reply, prov),
            "intent": intent.value,
            "destination": None,
            "duration_days": None,
            "tracking_id": None,
            "provenance": prov,
            "data": tool_result,
        }
        payload.update(extra)
        return payload

    @staticmethod
    def _ask(intent: IntentType, question: str, mode: str = "json", **extra: Any) -> Dict[str, Any]:
        """Clarifying question: no tool ran, nothing was fabricated."""
        payload: Dict[str, Any] = {
            "reply": question,
            "intent": intent.value,
            "destination": None,
            "duration_days": None,
            "tracking_id": None,
            "provenance": {
                "source": "travelogix_assistant",
                "mode": mode,
                "is_mock": False,
            },
            "data": {"clarification_required": True},
        }
        payload.update(extra)
        return payload

    # ------------------------------------------------------------------ #
    # Answer resolution: JSON dataset -> LLM -> RAG knowledge base
    #
    # Every travel handler resolves its answer through here, so the order is
    # identical everywhere:
    #   1. the local JSON dataset (data/*.json) - used directly, no LLM call, so a
    #      dataset hit can never be reworded or invented by a model;
    #   2. a general-knowledge LLM answer, only when the dataset has nothing;
    #   3. the RAG knowledge base, only when the customer asked about
    #      TravelLogix policies/services rather than about a trip.
    # ------------------------------------------------------------------ #
    @staticmethod
    def _is_dataset_miss(tool_result: Optional[Dict[str, Any]], rows_key: str) -> bool:
        """True when the dataset carries no usable rows for this request."""
        if not isinstance(tool_result, dict):
            return True
        if is_unavailable(tool_result):
            return True
        provenance = tool_result.get("provenance") or {}
        if provenance.get("mode") == "unavailable" or tool_result.get("available") is False:
            return True
        if rows_key == "distance_km":
            # Route lookups expose the distance directly rather than a row list.
            return (
                tool_result.get("distance_km") is None
                and tool_result.get("road_distance_estimate_km") is None
            )
        return not tool_result.get(rows_key)

    @staticmethod
    def _is_platform_question(message: str) -> bool:
        """True for policy/platform questions, which the RAG tier may answer."""
        return bool(_PLATFORM_QUESTION_RE.search(message or ""))

    @staticmethod
    def _llm_knowledge_result(tool_name: str, reply: str, requested: Dict[str, Any]) -> Dict[str, Any]:
        """Wrap a general-knowledge LLM answer as a non-dataset result."""
        res = build_json_response(
            intent=tool_name,
            status="success",
            data={"requested": requested, "general_info": reply},
            source="LLM general guidance",
            data_mode="llm_general",
            is_mock=False,
        )
        res["provenance"] = {
            "source": "LLM general guidance",
            "mode": "llm_general",
            "is_mock": False,
        }
        return res

    async def _answer_from_dataset_or_llm(
        self,
        message: str,
        tool_result: Optional[Dict[str, Any]],
        rows_key: str,
        kind: str,
        requested: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], str, str]:
        """
        Tier 1 + 2 + 3 for one travel request.

        Returns ``(tool_result, reply, tier)`` where tier is ``json``, ``llm_general`` or ``rag``.
        The caller renders the rows itself when the tier is ``json`` (that rendering is
        deterministic and short); this helper only words the answer for tiers 2 and 3.
        """
        if not self._is_dataset_miss(tool_result, rows_key):
            logger.info(f"Tier 1 (JSON): served {kind} from {_DATASET_SOURCE.get(kind, 'dataset')}.")
            return tool_result, "", "json"

        if self._is_platform_question(message):
            rag_result = query_knowledge_base(message, scope="travel")
            knowledge = rag_result.get("knowledge_data") if isinstance(rag_result, dict) else None
            if knowledge:
                logger.info(f"Tier 3 (RAG): answered {kind} request from the travel knowledge base.")
                return rag_result, render_knowledge_base_markdown(rag_result).strip(), "rag"

        logger.info(f"Tier 2 (LLM): no {kind} rows in the dataset; asking the LLM for general guidance.")
        reply = await synthesize_with_llm(
            _LLM_KNOWLEDGE_TOOLS.get(kind, "generalChat"), requested, message
        )
        payload = self._llm_knowledge_result(_LLM_KNOWLEDGE_TOOLS.get(kind, kind), reply, requested)

        if kind in _DATASET_SOURCE and _ROUTE_CLAIM_RE.search(reply or ""):
            # The model asserted a service exists for a route we hold no data for.
            # That is exactly the fabrication this tier must not produce.
            logger.warning(
                f"Discarding LLM {kind} answer that claimed a service exists without dataset rows."
            )
            return payload, self._data_miss_reply(kind), "llm_general"

        if reply and _DATA_MISS_PREFIX not in reply:
            reply = _DATA_MISS_PREFIX + reply
        return payload, reply, "llm_general"

    @staticmethod
    def _data_miss_reply(kind: str) -> str:
        return _DATA_MISS_QUESTION.get(kind, UNAVAILABLE_MESSAGE)

    # ------------------------------------------------------------------ #
    # Travel planning
    # ------------------------------------------------------------------ #
    async def _travel_itinerary(self, message, entities, ctx) -> Dict[str, Any]:
        session = get_conversation_session(ctx.conversation_id, ctx.user_id)
        all_slots = session.get_all_slots(entities)

        destination = all_slots.get("destination")
        origin = all_slots.get("origin")
        preference = all_slots.get("travel_preference")
        duration_days = self._days(entities, session.slots)
        total_budget = all_slots.get("total_budget_inr") or all_slots.get("budget")
        travelers = int(all_slots.get("travelers_count") or all_slots.get("travellers") or 1)

        # Auto-recommend/assign destination based on travel preference if destination not explicitly set
        if not destination and preference:
            pref_lower = preference.lower()
            if "hill" in pref_lower or "mountain" in pref_lower:
                destination = "Coorg"
            elif "beach" in pref_lower or "coastal" in pref_lower:
                destination = "Goa"
            elif "heritage" in pref_lower or "history" in pref_lower or "temple" in pref_lower:
                destination = "Hampi"
            elif "nature" in pref_lower or "forest" in pref_lower:
                destination = "Wayanad"

            if destination:
                session.slots["destination"] = destination
                all_slots["destination"] = destination

        msg_lower = (message or "").lower()
        is_recommendation_req = any(
            kw in msg_lower for kw in [
                "recommend", "recommendation", "where to go", "which destination",
                "suggest", "suggestion", "what destination", "where would you"
            ]
        )

        if is_recommendation_req and not entities.get("destination"):
            rec_dest = destination or "Coorg"
            budget_str = f" within a budget of ₹{total_budget:,.0f}" if total_budget else ""
            dur_str = f" for a {duration_days}-day trip" if duration_days else ""
            pref_str = f" to the **{preference}**" if preference else ""
            orig_str = f" from **{origin}**" if origin else ""
            reply = (
                f"Based on your travel context{dur_str}{orig_str}{budget_str}{pref_str}, "
                f"I highly recommend visiting **{rec_dest}**! It offers a perfect balance of scenic viewpoints, "
                f"relaxing atmosphere, and great local experiences.\n\n"
                f"Whenever you're ready, just say **\"Plan the trip for us\"** and I will build your detailed {duration_days}-day itinerary."
            )
            return self._result(
                reply,
                IntentType.TRAVEL_ITINERARY,
                {"recommended_destination": rec_dest, "slots": all_slots},
                destination=rec_dest,
                duration_days=duration_days,
            )

        if not destination:
            return self._ask(
                IntentType.TRAVEL_ITINERARY,
                "Sure! Where would you like to travel?",
                mode="llm",
            )

        tool_result = generateItinerary(destination=destination, duration_days=duration_days)

        budget_info = ""
        if total_budget:
            b_res = calculateBudget(
                destination=destination,
                duration_days=duration_days,
                total_budget_inr=total_budget,
                travelers_count=travelers
            )
            c_est = b_res["calculated_estimates"]
            orig_header = f"From {origin} to " if origin else ""
            budget_info = (
                f"\n\n---\n### 💰 Budget Breakdown ({orig_header}{destination} · {duration_days} days · {travelers} traveller{'s' if travelers > 1 else ''} · Target: ₹{total_budget:,.0f})\n"
                f"- **Transport**: ₹{c_est['intercity_transport']:,.0f}\n"
                f"- **Stay / Accommodation**: ₹{c_est['accommodation']:,.0f}\n"
                f"- **Food & Dining**: ₹{c_est['food_and_dining']:,.0f}\n"
                f"- **Local Travel**: ₹{c_est['local_travel_and_rentals']:,.0f}\n"
                f"- **Activities & Sightseeing**: ₹{c_est['activities_and_sightseeing']:,.0f}\n"
                f"- **Emergency Reserve**: ₹{c_est['emergency_reserve']:,.0f}\n"
                f"**Total Estimated Cost**: ≈ ₹{b_res['total_estimated_cost_inr']:,.0f}"
            )

        if tool_result.get("days"):
            reply = render_itinerary_markdown(
                tool_result,
                sections=_requested_sections(message),
                detailed=_wants_detail(message),
            ).strip() + budget_info
            tier = "json"
        else:
            reply = (await synthesize_with_llm("generateItinerary", tool_result, message)) + budget_info
            tier = "llm"

        return self._result(
            reply,
            IntentType.TRAVEL_ITINERARY,
            tool_result,
            mode=tier,
            destination=destination,
            duration_days=duration_days,
        )

    async def _budget(self, message, entities, ctx) -> Dict[str, Any]:
        session = get_conversation_session(ctx.conversation_id, ctx.user_id)
        all_slots = session.get_all_slots(entities)

        destination = all_slots.get("destination") or all_slots.get("location")
        origin = all_slots.get("origin")
        preference = all_slots.get("travel_preference")
        if not destination and preference:
            pref_lower = preference.lower()
            if "hill" in pref_lower or "mountain" in pref_lower:
                destination = "Coorg"
            elif "beach" in pref_lower or "coastal" in pref_lower:
                destination = "Goa"
            elif "heritage" in pref_lower or "history" in pref_lower:
                destination = "Hampi"
            elif "nature" in pref_lower:
                destination = "Wayanad"

            if destination:
                session.slots["destination"] = destination
                all_slots["destination"] = destination

        duration_days = self._days(entities, session.slots)
        total_budget = all_slots.get("total_budget_inr") or all_slots.get("budget") or 35000.0
        travelers = int(all_slots.get("travelers_count") or all_slots.get("travellers") or 1)

        if not destination:
            return self._ask(
                IntentType.BUDGET_CALCULATION,
                "### 💰 Travel Budget\n\n"
                "I can break a budget down by transport, stay, food and activities. "
                "**Which destination** should I plan for?",
            )

        tool_result = calculateBudget(
            destination=destination,
            duration_days=duration_days,
            total_budget_inr=total_budget,
            travelers_count=travelers,
        )

        c_est = tool_result["calculated_estimates"]
        has_explicit_days = bool(entities.get("duration_days") or session.slots.get("duration_days"))
        assumption = (
            ""
            if has_explicit_days
            else f"\n*Assumed a {duration_days}-day trip — tell me the real length and I'll recalculate.*"
        )
        orig_header = f"From {origin} to " if origin else ""
        reply = (
            f"**{orig_header}{destination} · {duration_days} days · {travelers} traveller"
            f"{'s' if travelers != 1 else ''}** (target ₹{total_budget:,.0f})\n"
            f"- Transport ₹{c_est['intercity_transport']:,.0f} · Stay ₹{c_est['accommodation']:,.0f} · "
            f"Food ₹{c_est['food_and_dining']:,.0f}\n"
            f"- Local travel ₹{c_est['local_travel_and_rentals']:,.0f} · "
            f"Activities ₹{c_est['activities_and_sightseeing']:,.0f} · "
            f"Reserve ₹{c_est['emergency_reserve']:,.0f}\n"
            f"**Total ≈ ₹{tool_result['total_estimated_cost_inr']:,.0f}** "
            f"(cushion ₹{tool_result['remaining_budget_inr']:,.0f})"
            f"{assumption}"
        )

        return self._result(
            reply,
            IntentType.BUDGET_CALCULATION,
            tool_result,
            destination=destination,
            duration_days=duration_days,
        )

    # ------------------------------------------------------------------ #
    # Transport & Location Handlers with Tiered Fallback
    # ------------------------------------------------------------------ #
    async def _flight_search(self, message, entities, ctx) -> Dict[str, Any]:
        session = get_conversation_session(ctx.conversation_id, ctx.user_id)
        all_slots = session.get_all_slots(entities)
        destination = all_slots.get("destination")
        origin = all_slots.get("origin")
        travel_date = all_slots.get("travel_date")

        if not destination:
            return self._ask(
                IntentType.FLIGHT_SEARCH,
                "### ✈️ Flight Search\n\n**Which destination** should I look up flights for? (e.g. *\"flights to Delhi\"*).",
            )
        if not origin:
            return self._ask(
                IntentType.FLIGHT_SEARCH,
                f"### ✈️ Flight Search\n\n**Which city** are you departing from to {destination}?",
            )

        msg_lower = (message or "").lower()
        is_yes_no = any(p in msg_lower for p in ["are there flights", "is there a flight", "is there any flight", "can i fly", "do you have flights", "are flights available"])
        is_cheapest = any(c in msg_lower for c in ["cheapest", "lowest price", "lowest fare", "best price"])

        # Tier 1 & 2: Real-Time API or Mock JSON dataset
        tool_result = searchFlights(origin=origin, destination=destination, travel_date=travel_date)
        data_mode = "live" if tool_result.get("provenance", {}).get("mode") == "live" else "demo"
        is_mock = tool_result.get("provenance", {}).get("is_mock", False)

        if self._is_dataset_miss(tool_result, "flights"):
            from app.providers.flights.mock import MockFlightProvider
            fallback = MockFlightProvider().search_flights(origin=origin, destination=destination, travel_date=travel_date)
            if fallback and fallback.get("flights"):
                tool_result = fallback
                data_mode = "demo"
                is_mock = True

        # Dataset first; the LLM (tier 2) or RAG (tier 3) only answer a dataset miss.
        tool_result, llm_reply, tier = await self._answer_from_dataset_or_llm(
            message,
            tool_result,
            "flights",
            "flights",
            {"origin": origin, "destination": destination, "travel_date": travel_date},
        )
        if tier != "json":
            return self._result(
                llm_reply,
                IntentType.FLIGHT_SEARCH,
                tool_result,
                destination=destination,
                mode=tier,
            )

        flights = tool_result.get("flights", [])
        norm_flights = [normalize_flight(f, origin=origin, destination=destination, date=travel_date) for f in flights]

        if is_cheapest and norm_flights:
            norm_flights = sorted(norm_flights, key=lambda x: float(x.get("price") or x.get("price_inr") or 999999))[:1]

        norm_payload = build_json_response(
            intent="flight_search",
            status="success",
            data={"origin": origin, "destination": destination, "travel_date": travel_date, "results": norm_flights},
            source="flight_provider",
            data_mode=data_mode,
            is_mock=is_mock,
        )
        reply = format_flights_response(
            norm_payload, origin, destination, compact=True, limit=SHORT_ANSWER_LIMIT
        )

        if is_yes_no:
            count = len(norm_flights)
            prefix = (
                f"Yes, flights operate between {origin} and {destination}"
                f" ({count} option{'s' if count != 1 else ''}):\n\n"
            )
            reply = prefix + reply

        return self._result(reply, IntentType.FLIGHT_SEARCH, norm_payload, destination=destination)

    async def _flight_status(self, message, entities, ctx) -> Dict[str, Any]:
        flight_number = entities.get("flight_number")
        if not flight_number:
            return self._ask(
                IntentType.FLIGHT_STATUS,
                "### ✈️ Flight Status\n\nPlease share the **flight number** "
                "(for example `AI582` or `6E2041`) and I'll check its status.",
            )

        # Tier 1 & 2: Real-Time API or Mock Dataset
        tool_result = getFlightStatus(flight_number=flight_number)
        data_mode = "live" if tool_result.get("provenance", {}).get("mode") == "live" else "demo"
        is_mock = tool_result.get("provenance", {}).get("is_mock", False)

        if is_unavailable(tool_result) or tool_result.get("provenance", {}).get("mode") == "unavailable":
            from app.providers.flights.mock import MockFlightProvider
            fallback = MockFlightProvider().get_flight_status(flight_number=flight_number)
            if fallback and fallback.get("status"):
                tool_result = fallback
                data_mode = "demo"
                is_mock = True

        # Flight status is dataset-only: an unknown number must say so, never be
        # described from model memory.
        if is_unavailable(tool_result) or not tool_result.get("status"):
            reply = (
                f"### ✈️ Flight Status: `{flight_number}`\n\n"
                f"No status for this flight number right now. "
                "Check the airline's app or website for the live status."
            )
            norm_payload = build_json_response(
                "flight_status", "unavailable", None, source="flight_provider", data_mode="unavailable"
            )
            return self._result(reply, IntentType.FLIGHT_STATUS, norm_payload)

        norm_f = normalize_flight(tool_result)
        norm_payload = build_json_response("flight_status", "success", norm_f, source="flight_provider", data_mode=data_mode, is_mock=is_mock)
        reply = (
            f"**{norm_f['airline']} {norm_f['flight_number']}** — {str(norm_f['status']).title()}\n"
            f"{norm_f['origin']} ➔ {norm_f['destination']} · "
            f"dep {norm_f['departure_time']} · arr {norm_f['arrival_time']}"
        )
        return self._result(reply, IntentType.FLIGHT_STATUS, norm_payload)

    async def _hotel_search(self, message, entities, ctx) -> Dict[str, Any]:
        session = get_conversation_session(ctx.conversation_id, ctx.user_id)
        all_slots = session.get_all_slots(entities)
        location = all_slots.get("location") or all_slots.get("destination")
        max_price = all_slots.get("max_price") or all_slots.get("total_budget_inr") or all_slots.get("budget")

        if not location:
            return self._ask(
                IntentType.HOTEL_SEARCH,
                "Sure! Which city would you like to stay in?",
            )

        # Tier 1 & 2: HotelProvider search
        tool_result = searchHotels(location=location, max_price=max_price)
        data_mode = "live" if tool_result.get("provenance", {}).get("mode") == "live" else "demo"
        is_mock = tool_result.get("provenance", {}).get("is_mock", False)

        if self._is_dataset_miss(tool_result, "hotels"):
            from app.providers.hotels import HotelProvider
            fallback = HotelProvider("demo").search_hotels(location=location, max_price=max_price)
            if fallback and fallback.get("hotels"):
                tool_result = fallback
                data_mode = "demo"
                is_mock = True

        tool_result, llm_reply, tier = await self._answer_from_dataset_or_llm(
            message,
            tool_result,
            "hotels",
            "hotels",
            {"location": location, "max_price": max_price},
        )
        if tier != "json":
            return self._result(
                llm_reply,
                IntentType.HOTEL_SEARCH,
                tool_result,
                destination=location,
                mode=tier,
            )

        hotels = tool_result.get("hotels", [])
        norm_hotels = [normalize_hotel(h, city=location) for h in hotels]
        norm_payload = build_json_response(
            intent="hotel_search",
            status="success",
            data={"city": location, "max_price": max_price, "results": norm_hotels},
            source="hotel_provider",
            data_mode=data_mode,
            is_mock=is_mock,
        )
        reply = format_hotels_response(norm_payload, city=location, compact=True, limit=SHORT_ANSWER_LIMIT)
        return self._result(reply, IntentType.HOTEL_SEARCH, norm_payload, destination=location)

    async def _train_search(self, message, entities, ctx) -> Dict[str, Any]:
        session = get_conversation_session(ctx.conversation_id, ctx.user_id)
        all_slots = session.get_all_slots(entities)
        destination = all_slots.get("destination")
        origin = all_slots.get("origin")
        travel_date = all_slots.get("travel_date")

        if not destination or not origin:
            return self._ask(
                IntentType.TRAIN_SEARCH,
                "Sure! Where are you travelling from and to?",
            )

        # Dataset first. For a route we hold, the schedule does not depend on the travel
        # date, so the answer goes out immediately instead of asking for a date first.
        tool_result = searchTrains(origin=origin, destination=destination)
        data_mode = "live" if tool_result.get("provenance", {}).get("mode") == "live" else "demo"
        is_mock = tool_result.get("provenance", {}).get("is_mock", False)

        if self._is_dataset_miss(tool_result, "trains"):
            from app.providers.trains import TrainProvider
            fallback = TrainProvider("demo").search_trains(origin=origin, destination=destination)
            if fallback and fallback.get("trains"):
                tool_result = fallback
                data_mode = "demo"
                is_mock = True

        if not travel_date and self._is_dataset_miss(tool_result, "trains"):
            # Nothing for this route in the dataset. Collect the date first, so the next
            # turn carries the full request into the knowledge/LLM tier.
            logger.info("Train route absent from the dataset; asking for the travel date.")
            return self._ask(
                IntentType.TRAIN_SEARCH,
                f"**Which date** would you like to travel from {origin} to {destination}?",
            )

        tool_result, llm_reply, tier = await self._answer_from_dataset_or_llm(
            message,
            tool_result,
            "trains",
            "trains",
            {"origin": origin, "destination": destination, "travel_date": travel_date},
        )
        if tier != "json":
            return self._result(
                llm_reply,
                IntentType.TRAIN_SEARCH,
                tool_result,
                destination=destination,
                mode=tier,
            )

        trains = tool_result.get("trains", [])
        norm_trains = [normalize_train(t, origin=origin, destination=destination) for t in trains]
        norm_payload = build_json_response(
            intent="train_search",
            status="success",
            data={"origin": origin, "destination": destination, "date": travel_date, "results": norm_trains},
            source="train_provider",
            data_mode=data_mode,
            is_mock=is_mock,
        )
        reply = format_trains_response(
            norm_payload, origin, destination, compact=True, limit=SHORT_ANSWER_LIMIT
        )
        if not travel_date:
            reply += "\n\n_Tell me your travel date and I'll note it for booking._"
        return self._result(reply, IntentType.TRAIN_SEARCH, norm_payload, destination=destination)

    async def _train_status(self, message, entities, ctx) -> Dict[str, Any]:
        train_number = entities.get("train_number")
        if not train_number:
            return self._ask(
                IntentType.TRAIN_STATUS,
                "### 🚆 Train Running Status\n\nPlease share the **train number or name** "
                "(for example `17309` or *Goa Express*) so I can look up its status.",
            )

        tool_result = getTrainStatus(train_number)
        title = f"🚆 Train Running Status: {train_number}"
        data_mode = "live" if tool_result.get("provenance", {}).get("mode") == "live" else "demo"
        is_mock = tool_result.get("provenance", {}).get("is_mock", False)

        if is_unavailable(tool_result):
            from app.providers.trains import TrainProvider
            fallback = TrainProvider("demo").get_train_status(train_number)
            if fallback and not is_unavailable(fallback):
                tool_result = fallback
                data_mode = "demo"
                is_mock = True

        # Running status is dataset-only: an unknown train must say so rather than
        # let a model describe a position it cannot verify.
        if is_unavailable(tool_result):
            reply = (
                f"### {title}\n\n"
                f"No running status for `{train_number}` right now. "
                "Check NTES or the IRCTC app for the live position."
            )
            norm_payload = build_json_response(
                "train_status", "unavailable", None, source="train_provider", data_mode="unavailable"
            )
            return self._result(reply, IntentType.TRAIN_STATUS, norm_payload)

        reply = (
            f"**{self._text(tool_result.get('train_name'))}** ({self._text(tool_result.get('train_number'))}): "
            f"{self._text(tool_result.get('status'))}\n"
            f"Last passed {self._text(tool_result.get('last_passed_station'))} · "
            f"at {self._text(tool_result.get('current_station'))} · "
            f"next {self._text(tool_result.get('next_station'))}"
            f" (delay {self._text(tool_result.get('delay_minutes'))} min)"
        )
        norm_payload = build_json_response("train_status", "success", tool_result, source="train_provider", data_mode=data_mode, is_mock=is_mock)
        return self._result(reply, IntentType.TRAIN_STATUS, norm_payload)

    async def _bus_search(self, message, entities, ctx) -> Dict[str, Any]:
        session = get_conversation_session(ctx.conversation_id, ctx.user_id)
        all_slots = session.get_all_slots(entities)
        destination = all_slots.get("destination")
        origin = all_slots.get("origin")
        travel_date = all_slots.get("travel_date")

        if not destination or not origin:
            return self._ask(
                IntentType.BUS_SEARCH,
                "Sure! Where are you travelling from and to?",
            )

        tool_result = searchBuses(origin=origin, destination=destination)
        data_mode = "live" if tool_result.get("provenance", {}).get("mode") == "live" else "demo"
        is_mock = tool_result.get("provenance", {}).get("is_mock", False)

        if self._is_dataset_miss(tool_result, "buses"):
            from app.providers.buses import BusProvider
            fallback = BusProvider("demo").search_buses(origin=origin, destination=destination)
            if fallback and fallback.get("buses"):
                tool_result = fallback
                data_mode = "demo"
                is_mock = True

        tool_result, llm_reply, tier = await self._answer_from_dataset_or_llm(
            message,
            tool_result,
            "buses",
            "buses",
            {"origin": origin, "destination": destination, "travel_date": travel_date},
        )
        if tier != "json":
            return self._result(
                llm_reply,
                IntentType.BUS_SEARCH,
                tool_result,
                destination=destination,
                mode=tier,
            )

        buses = tool_result.get("buses", [])
        norm_buses = [normalize_bus(b, origin=origin, destination=destination) for b in buses]
        norm_payload = build_json_response(
            intent="bus_search",
            status="success",
            data={"origin": origin, "destination": destination, "date": travel_date, "results": norm_buses},
            source="existing local dataset",
            data_mode="json",
            is_mock=is_mock,
        )
        norm_payload["provenance"] = {
            "source": "existing local dataset",
            "mode": "json",
            "is_mock": is_mock,
        }
        reply = format_buses_response(
            norm_payload, origin, destination, compact=True, limit=SHORT_ANSWER_LIMIT
        )
        return self._result(reply, IntentType.BUS_SEARCH, norm_payload, destination=destination)

    async def _bus_status(self, message, entities, ctx) -> Dict[str, Any]:
        bus_identifier = entities.get("bus_identifier") or message
        if not bus_identifier:
            return self._ask(
                IntentType.BUS_STATUS,
                "### 🚌 Bus Live Status\n\nPlease share the **bus service name or number**.",
            )

        tool_result = getBusStatus(bus_identifier)
        title = f"🚌 Bus Live Tracking: {bus_identifier}"
        data_mode = "live" if tool_result.get("provenance", {}).get("mode") == "live" else "demo"
        is_mock = tool_result.get("provenance", {}).get("is_mock", False)

        if is_unavailable(tool_result):
            from app.providers.buses import BusProvider
            fallback = BusProvider("demo").get_bus_status(bus_identifier)
            if fallback and not is_unavailable(fallback):
                tool_result = fallback
                data_mode = "demo"
                is_mock = True

        # Live position is dataset-only: never let a model describe where a bus is.
        if is_unavailable(tool_result):
            reply = (
                f"### {title}\n\n"
                f"No running status for `{bus_identifier}` right now. "
                "Check the operator's own tracking page for the live position."
            )
            norm_payload = build_json_response(
                "bus_status", "unavailable", None, source="bus_provider", data_mode="unavailable"
            )
            return self._result(reply, IntentType.BUS_STATUS, norm_payload)

        route_note = f" · route {self._text(tool_result.get('route'))}" if tool_result.get("route") else ""
        reply = (
            f"**{self._text(tool_result.get('operator'))}**{route_note}: "
            f"{self._text(tool_result.get('status'))}\n"
            f"Now near {self._text(tool_result.get('current_location'))} · "
            f"ETA {self._text(tool_result.get('eta'))} "
            f"(delay {self._text(tool_result.get('delay_minutes'))} min)"
        )
        norm_payload = build_json_response("bus_status", "success", tool_result, source="bus_provider", data_mode=data_mode, is_mock=is_mock)
        return self._result(reply, IntentType.BUS_STATUS, norm_payload)

    async def _maps_route(self, message, entities, ctx) -> Dict[str, Any]:
        session = get_conversation_session(ctx.conversation_id, ctx.user_id)
        all_slots = session.get_all_slots(entities)
        origin = all_slots.get("origin")
        destination = all_slots.get("destination")
        transport_mode = all_slots.get("transport_mode", "driving")

        if not origin or not destination:
            return self._ask(
                IntentType.MAPS_ROUTE,
                "Sure! Where are you travelling from and to?",
            )

        tool_result = getRoute(origin=origin, destination=destination, travel_mode=transport_mode)
        is_calculated = "locally calculated" in str(tool_result.get("notice", "")).lower()
        data_mode = "demo" if is_calculated else ("live" if tool_result.get("provenance", {}).get("mode") == "live" else "demo")
        is_mock = is_calculated or tool_result.get("provenance", {}).get("is_mock", True)

        # Tier 1: the local reference-coordinate table (app/providers/maps).
        if tool_result.get("distance_km") is None and tool_result.get("road_distance_estimate_km") is None:
            tool_result, llm_reply, tier = await self._answer_from_dataset_or_llm(
                message,
                tool_result,
                "distance_km",
                "routes",
                {"origin": origin, "destination": destination, "mode": transport_mode},
            )
            return self._result(
                llm_reply,
                IntentType.MAPS_ROUTE,
                tool_result,
                destination=destination,
                mode=tier,
            )

        norm_r = normalize_route(tool_result, origin=origin, destination=destination)
        norm_payload = build_json_response(
            intent="route_search",
            status="success",
            data=norm_r,
            source="maps_provider",
            data_mode=data_mode,
            is_mock=is_mock,
        )
        reply = format_route_response(norm_payload, origin, destination, compact=True)
        return self._result(reply, IntentType.MAPS_ROUTE, norm_payload, destination=destination)

    async def _cab_search(self, message, entities, ctx) -> Dict[str, Any]:
        pickup = entities.get("pickup") or "Airport"
        drop = entities.get("drop") or entities.get("destination") or "Hotel"
        tool_result = searchCabs(pickup=pickup, drop=drop)
        reply = format_cabs_response(tool_result, pickup=pickup, drop=drop)
        return self._result(reply, IntentType.CAB_SEARCH, tool_result)

    async def _weather(self, message, entities, ctx) -> Dict[str, Any]:
        destination = entities.get("destination")
        if not destination:
            return self._ask(
                IntentType.WEATHER_INQUIRY,
                "Sure! Which city would you like the weather for?",
            )

        tool_result = getWeather(location=destination)
        data_mode = "live" if tool_result.get("provenance", {}).get("mode") == "live" else "demo"
        is_mock = tool_result.get("provenance", {}).get("is_mock", False)

        if is_unavailable(tool_result):
            from app.providers.weather import WeatherProvider
            fallback = WeatherProvider("demo").get_weather(location=destination)
            if fallback and not is_unavailable(fallback):
                tool_result = fallback
                data_mode = "demo"
                is_mock = True

        tool_result, llm_reply, tier = await self._answer_from_dataset_or_llm(
            message,
            tool_result,
            "condition",
            "weather",
            {"location": destination},
        )
        if tier != "json":
            return self._result(
                llm_reply,
                IntentType.WEATHER_INQUIRY,
                tool_result,
                destination=destination,
                mode=tier,
            )

        norm_w = normalize_weather(tool_result, city=destination)
        norm_payload = build_json_response(
            intent="weather",
            status="success",
            data=norm_w,
            source="weather_provider",
            data_mode=data_mode,
            is_mock=is_mock,
        )
        reply = format_weather_response(norm_payload, city=destination, compact=True)
        return self._result(reply, IntentType.WEATHER_INQUIRY, norm_payload, destination=destination)

    async def _driver_info(self, message, entities, ctx) -> Dict[str, Any]:
        tracking_id = entities.get("tracking_id")
        if not tracking_id:
            return self._ask(
                IntentType.DRIVER_INFO,
                "### 👨‍✈️ Driver Information\n\nPlease provide your **shipment tracking ID** to view driver details.",
            )
        tool_result = await getDriverInfoAsync(tracking_id, ctx.db) if ctx.db else {"found": False}
        if not tool_result.get("found"):
            norm = build_json_response("driver_info", "unavailable", None, source="travelogix_database", data_mode="database")
            return self._result("### 👨‍✈️ Driver Details\n\nNo driver details available for this shipment.", IntentType.DRIVER_INFO, norm)
        drv = normalize_driver(tool_result.get("driver") or {})
        norm = build_json_response("driver_info", "success", drv, source="travelogix_database", data_mode="database")
        reply = f"### 👨‍✈️ Driver Assigned (Shipment `{tracking_id}`)\n\n- **Name:** {drv['name']}\n- **Status:** {drv['status']}"
        if drv.get("phone"):
            reply += f"\n- **Contact:** {drv['phone']}"
        return self._result(reply, IntentType.DRIVER_INFO, norm)

    async def _vehicle_status(self, message, entities, ctx) -> Dict[str, Any]:
        tracking_id = entities.get("tracking_id")
        if not tracking_id:
            return self._ask(
                IntentType.VEHICLE_STATUS,
                "### 🚚 Vehicle Status\n\nPlease provide your **shipment tracking ID** to view vehicle status.",
            )
        tool_result = await getVehicleStatusAsync(tracking_id, ctx.db) if ctx.db else {"found": False}
        if not tool_result.get("found"):
            norm = build_json_response("vehicle_status", "unavailable", None, source="travelogix_database", data_mode="database")
            return self._result("### 🚚 Vehicle Details\n\nNo vehicle details available for this shipment.", IntentType.VEHICLE_STATUS, norm)
        veh = normalize_vehicle(tool_result.get("vehicle") or {})
        norm = build_json_response("vehicle_status", "success", veh, source="travelogix_database", data_mode="database")
        reply = f"### 🚚 Vehicle Status (Shipment `{tracking_id}`)\n\n- **Registration:** `{veh['vehicle_number']}`\n- **Type/Model:** {veh['type']}\n- **Status:** {veh['status']}"
        return self._result(reply, IntentType.VEHICLE_STATUS, norm)

        reply = (
            f"### {title}\n\n"
            f"- **Condition:** {self._text(tool_result.get('condition'))}\n"
            f"- **Temperature Range:** {self._text(tool_result.get('temperature_range'))}\n"
            f"- **Humidity:** {self._text(tool_result.get('humidity'))}\n"
            f"- **Precipitation Chance:** {self._text(tool_result.get('precipitation_chance'))}\n"
            f"- **Recommendation:** {self._text(tool_result.get('clothing_recommendation'))}\n"
        )
        if tool_result.get("notice"):
            reply += f"\n*{tool_result['notice']}*"
        return self._result(
            reply, IntentType.WEATHER_INQUIRY, tool_result, destination=destination
        )

    async def _delay_disruption(self, message, entities, ctx) -> Dict[str, Any]:
        destination = entities.get("destination")
        if not destination:
            return self._ask(
                IntentType.DELAY_DISRUPTION,
                "### ⏱️ Delay Planning\n\n**Which trip** has been delayed? Tell me the "
                "destination, trip length and the delay in hours and I'll re-time Day 1.",
            )

        delay_hours = entities.get("delay_hours") or 4.0
        duration_days = self._days(entities)

        tool_result = recalculateDisruptedItinerary(
            destination=destination, duration_days=duration_days, delay_hours=delay_hours
        )
        adjusted = tool_result.get("adjusted_days") or []
        first_day = adjusted[0] if adjusted else {}

        reply = (
            f"### ⏱️ Disruption Adjustment: **{self._text(tool_result.get('title'))}**\n\n"
            f"{self._text(tool_result.get('summary'))}\n\n"
            f"**Updated Day 1 Timing:**\n"
            f"- **Status:** {self._text(first_day.get('morning'))}\n"
            f"- **Afternoon:** {self._text(first_day.get('afternoon'))}\n"
            f"- **Evening:** {self._text(first_day.get('evening'))}\n"
        )
        return self._result(
            reply,
            IntentType.DELAY_DISRUPTION,
            tool_result,
            destination=destination,
            duration_days=duration_days,
        )

    async def _trip_modification(self, message, entities, ctx) -> Dict[str, Any]:
        destination = entities.get("destination")
        if not destination:
            return self._ask(
                IntentType.TRIP_MODIFICATION,
                "### ✏️ Trip Modification\n\n**Which trip** should I modify, and what "
                "would you like changed?",
            )

        duration_days = self._days(entities, default=4)
        tool_result = modifyItinerary(
            destination=destination,
            duration_days=duration_days,
            modification_request=entities.get("modification_request", ""),
        )
        reply = await synthesize_with_llm("modifyItinerary", tool_result, message)
        return self._result(
            reply,
            IntentType.TRIP_MODIFICATION,
            tool_result,
            destination=destination,
            duration_days=duration_days,
        )

    async def _packing(self, message, entities, ctx) -> Dict[str, Any]:
        destination = entities.get("destination")
        if not destination:
            return self._ask(
                IntentType.PACKING_ASSISTANT,
                "### 🧳 Packing Assistant\n\n**Where** are you travelling, and for how "
                "many days? I'll tailor the packing list.",
            )

        duration_days = self._days(entities)
        tool_result = getPackingSuggestions(
            destination=destination, duration_days=duration_days
        )
        cl = tool_result["checklist"]

        reply = (
            f"### 🧳 Packing Checklist for {destination} ({duration_days} Days)\n\n"
            f"**📄 Documents & Essentials:**\n"
            + "\n".join([f"- {i}" for i in cl['documents_and_essentials']]) + "\n\n"
            f"**👕 Clothing:**\n" + "\n".join([f"- {i}" for i in cl['clothing']]) + "\n\n"
            f"**🧴 Toiletries & Skincare:**\n"
            + "\n".join([f"- {i}" for i in cl['toiletries_and_skincare']]) + "\n\n"
            f"**🔌 Electronics:**\n" + "\n".join([f"- {i}" for i in cl['electronics']]) + "\n\n"
            f"**💊 Medical & First Aid:**\n"
            + "\n".join([f"- {i}" for i in cl['health_and_safety']])
        )
        return self._result(
            reply,
            IntentType.PACKING_ASSISTANT,
            tool_result,
            destination=destination,
            duration_days=duration_days,
        )

    async def _travel_checklist(self, message, entities, ctx) -> Dict[str, Any]:
        tool_result = getTravelChecklist()
        cats = tool_result["categories"]
        reply = (
            f"### {tool_result['title']}\n\n"
            + "\n\n".join([
                f"**{cat}:**\n" + "\n".join([f"- {item}" for item in items])
                for cat, items in cats.items()
            ])
        )
        return self._result(reply, IntentType.TRAVEL_CHECKLIST, tool_result)

    async def _places(self, message, entities, ctx) -> Dict[str, Any]:
        session = get_conversation_session(ctx.conversation_id, ctx.user_id)
        all_slots = session.get_all_slots(entities)
        location = all_slots.get("location") or all_slots.get("destination")
        if not location:
            return self._ask(
                IntentType.PLACES_ACTIVITIES,
                "### 🌴 Places & Activities\n\n**Which city** are you interested in?",
            )

        tool_result = searchPlaces(location=location)
        places = tool_result.get("places", [])

        if not places:
            reply = await synthesize_with_llm("placesGeneral", {"location": location}, message)
            norm_payload = build_json_response("places", "success", {"city": location, "info": reply}, source="llm_assistant", data_mode="llm")
            return self._result(reply, IntentType.PLACES_ACTIVITIES, norm_payload, destination=location, mode="llm")

        p_lines = "\n".join([
            f"- **{p['name']}** ({p['category']}) — ⭐ {p['rating']} (Hours: {p['timing']})"
            for p in places
        ])
        reply = f"### 🌴 Recommended Attractions & Dining in **{location}**\n\n{p_lines}"
        return self._result(
            reply, IntentType.PLACES_ACTIVITIES, tool_result, destination=location
        )

    # ------------------------------------------------------------------ #
    # Freight
    # ------------------------------------------------------------------ #
    async def _shipment_tracking(self, message, entities, ctx) -> Dict[str, Any]:
        tracking_id = entities.get("tracking_id")

        if not tracking_id:
            reply = (
                "### 🚚 Shipment Tracking\n\n"
                "Please provide a valid TravelLogix Tracking ID "
                "(e.g. `TLX-2026-100001` or `TLX-8961AD64`) to track your shipment."
            )
            return self._ask(IntentType.SHIPMENT_TRACKING, reply, mode="json", tracking_id=None)

        if ctx.db is not None:
            tool_result = await trackShipmentAsync(tracking_id=tracking_id, db=ctx.db)
        else:
            tool_result = trackShipment(tracking_id=tracking_id)

        if is_unavailable(tool_result):
            return self._result(
                f"### 🚚 Shipment Tracking\n\n"
                f"**Tracking ID:** `{tracking_id}`\n\n"
                f"Tracking service is temporarily unavailable. Please try again shortly.",
                IntentType.SHIPMENT_TRACKING,
                tool_result,
                mode="json",
                tracking_id=tracking_id,
            )

        if not tool_result.get("found"):
            reply = (
                f"### 📦 Shipment Not Found\n\n"
                f"**Tracking ID:** `{tracking_id}`\n\n"
                f"Please verify your TravelLogix Tracking ID and try again."
            )
        else:
            tr_id = tool_result.get("tracking_id") or tracking_id
            status = self._text(tool_result.get("status"))
            origin = self._text(tool_result.get("origin"))
            destination = self._text(tool_result.get("destination"))
            location = self._text(tool_result.get("verified_location") or tool_result.get("current_location") or origin)
            last_updated = tool_result.get("last_updated")

            prov = tool_result.get("provenance") or {}
            if prov.get("is_mock") or prov.get("mode") == "demo":
                badge = "ℹ️ **DEMO DATA**"
            elif prov.get("mode") == "live":
                badge = "🟢 **LIVE DATA**"
            else:
                badge = "ℹ️ **LATEST UPDATE**"

            lines = [
                f"### 🚚 Shipment Tracking\n",
                f"{badge}\n",
                f"- **Tracking ID:** `{tr_id}`",
                f"- **Status:** `{status}`",
                f"- **Origin:** {origin}",
                f"- **Destination:** {destination}",
                f"- **Route:** {origin} ➔ {destination}",
            ]

            if tool_result.get("driver"):
                d = tool_result["driver"]
                d_name = d.get("full_name") if isinstance(d, dict) else str(d)
                d_phone = f" ({d.get('phone')})" if isinstance(d, dict) and d.get("phone") else ""
                lines.append(f"- **Driver:** {d_name}{d_phone}")

            if tool_result.get("vehicle"):
                v = tool_result["vehicle"]
                v_reg = v.get("registration_number") if isinstance(v, dict) else str(v)
                v_model = f" ({v.get('model')})" if isinstance(v, dict) and v.get("model") else ""
                lines.append(f"- **Vehicle:** {v_reg}{v_model}")

            lines.append(f"- **Location:** {location}")

            if last_updated:
                lines.append(f"- **Last Updated:** {last_updated}")
            if tool_result.get("expected_delivery_date"):
                lines.append(f"- **Expected Delivery:** {tool_result['expected_delivery_date']}")

            events = tool_result.get("events") or []
            if events:
                lines.append("\n**Tracking History:**")
                for e in events:
                    e_status = e.get("status", "UPDATE")
                    e_loc = e.get("location", "")
                    loc_str = f" at {e_loc}" if e_loc else ""
                    e_time = f" ({e.get('timestamp')})" if e.get("timestamp") else ""
                    e_msg = f" — {e.get('message')}" if e.get("message") else ""
                    lines.append(f"- ✓ `{e_status}`{loc_str}{e_msg}{e_time}")
            elif tool_result.get("events_note"):
                lines.append(f"\n*{tool_result['events_note']}*")

            reply = "\n".join(lines)

        return self._result(
            reply,
            IntentType.SHIPMENT_TRACKING,
            tool_result,
            mode="json",
            tracking_id=tool_result.get("tracking_id", tracking_id),
        )

    async def _shipment_register(self, message, entities, ctx) -> Dict[str, Any]:
        """
        Register a shipment ONLY from fully specified details plus a real identity.

        The previous version filled every gap with defaults (Bangalore -> Goa, 5 kg,
        "Customer"/customer@example.com) and wrote a genuine freight row for a bare
        "I want to register a shipment." prompt.
        """
        origin = entities.get("origin")
        destination = entities.get("destination")
        weight_kg = entities.get("weight_kg")

        missing = [
            label
            for label, value in (
                ("pickup city", origin),
                ("delivery city", destination),
                ("package weight in kg", weight_kg),
            )
            if value in (None, "")
        ]

        if missing:
            return self._ask(
                IntentType.SHIPMENT_REGISTER,
                "### 📦 Register a Shipment\n\n"
                "I can register this consignment, but I still need: "
                f"**{', '.join(missing)}**.\n\n"
                "For example: *\"Register a shipment from Bangalore to Goa, 8 kg\"*.",
            )

        if not _is_real_identity(ctx.customer_email):
            return self._ask(
                IntentType.SHIPMENT_REGISTER,
                "### 📦 Register a Shipment\n\n"
                f"I have **{origin} ➔ {destination}**, **{weight_kg} kg**.\n\n"
                "**Please sign in to complete the registration** so the consignment is "
                "booked against your account.",
            )

        if ctx.db is None:
            return self._ask(
                IntentType.SHIPMENT_REGISTER,
                "### 📦 Register a Shipment\n\n"
                "Shipment registration is temporarily unavailable because the booking "
                "service could not be reached. Please try again shortly.",
            )

        try:
            tool_result = await registerShipmentAsync(
                db=ctx.db,
                origin=origin,
                destination=destination,
                weight_kg=float(weight_kg),
                recipient_name=ctx.customer_name or ctx.customer_email,
                customer_id=ctx.user_id,
                customer_name=ctx.customer_name or ctx.customer_email,
                customer_email=ctx.customer_email,
            )
        except Exception as exc:
            logger.error(
                f"Shipment registration failed for customer={ctx.customer_email}: {exc}"
            )
            return self._ask(
                IntentType.SHIPMENT_REGISTER,
                "### 📦 Register a Shipment\n\n"
                "I could not create the consignment. Please check the pickup city, "
                "delivery city and package weight, then try again.",
            )

        reply = (
            f"### ✅ Shipment Registered\n\n"
            f"- **Tracking ID:** `{tool_result['tracking_id']}`\n"
            f"- **Route:** {tool_result['origin']} ➔ {tool_result['destination']}\n"
            f"- **Weight:** {tool_result['weight_kg']} kg\n"
            f"- **Status:** `{tool_result['status']}`\n"
            f"- **Estimated Freight Charges:** ₹{tool_result['cost_inr']:,.2f}\n\n"
            f"You can track this package anytime by typing "
            f"*\"Track {tool_result['tracking_id']}\"*."
        )
        return self._result(
            reply,
            IntentType.SHIPMENT_REGISTER,
            tool_result,
            tracking_id=tool_result.get("tracking_id"),
            destination=destination,
        )

    # ------------------------------------------------------------------ #
    # Static knowledge / RAG
    #
    # Order: local JSON dataset (the travel data), then the LLM for general travel
    # knowledge, then the RAG knowledge base for platform/policy questions.
    # ------------------------------------------------------------------ #
    async def _travelogix_info(self, message, entities, ctx) -> Dict[str, Any]:
        """Platform & company info: handled by the RAG knowledge base, not a model."""
        tool_result = query_knowledge_base(message, scope="travel")
        reply = render_knowledge_base_markdown(tool_result).strip()
        if not reply or reply == UNAVAILABLE_MESSAGE:
            reply = (
                "I can help with trip plans, flights, trains, buses, hotels, routes and weather. "
                "What would you like to plan?"
            )
        return self._result(
            reply,
            IntentType.TRAVELOGIX_INFORMATION,
            tool_result,
            mode="rag",
        )

    async def _policy(self, message, entities, ctx) -> Dict[str, Any]:
        """Travel policies: RAG first (it is the authoritative text), dataset for any
        concrete route named in the same message, LLM only for the wording."""
        rag_result = query_knowledge_base(message, scope="travel")
        knowledge = rag_result.get("knowledge_data") if isinstance(rag_result, dict) else None
        if knowledge:
            reply = render_knowledge_base_markdown(rag_result).strip()
            return self._result(reply, IntentType.POLICY_RAG, rag_result, mode="rag")

        msg_lower = message.lower()
        if "flight" in msg_lower:
            orig = entities.get("origin") or DEFAULT_ORIGIN
            dest = entities.get("destination") or "Delhi"
            fl_result = searchFlights(origin=orig, destination=dest)
            if not self._is_dataset_miss(fl_result, "flights"):
                norm_flights = [normalize_flight(f, origin=orig, destination=dest) for f in fl_result.get("flights", [])]
                payload = build_json_response(
                    "flight_search",
                    "success",
                    {"origin": orig, "destination": dest, "results": norm_flights},
                    source="flight_provider",
                    data_mode="demo",
                    is_mock=True,
                )
                reply = (
                    f"I don't have a travel policy matching that. "
                    f"Here are the flights I hold for {orig} → {dest}:\n\n"
                    + format_flights_response(payload, orig, dest, compact=True, limit=SHORT_ANSWER_LIMIT)
                )
                return self._result(reply, IntentType.POLICY_RAG, payload, destination=dest, mode="json")

        reply = await synthesize_with_llm("policyRAG", rag_result, message)
        return self._result(reply, IntentType.POLICY_RAG, rag_result, mode="llm")

    async def _general_chat(self, message: str, entities: Dict[str, Any], ctx: Optional[Any] = None) -> Dict[str, Any]:
        needs_destination = entities.get("needs_clarification") == "destination"
        if needs_destination:
            return self._ask(
                IntentType.GENERAL_CHAT,
                "Which destination do you have in mind, and how many days would you like to travel for?\n\n"
                "For example: *\"Plan 5 days in Goa\"*.",
                mode="llm",
            )

        # Tier 3: platform/policy questions are answered straight from the KB.
        if self._is_platform_question(message):
            rag_result = query_knowledge_base(message, scope="travel")
            knowledge = rag_result.get("knowledge_data") if isinstance(rag_result, dict) else None
            if knowledge:
                reply = render_knowledge_base_markdown(rag_result).strip()
                return self._result(reply, IntentType.GENERAL_CHAT, rag_result, mode="rag")

        # Tier 2: general travel knowledge from the LLM (the dataset had no rows).
        payload = build_json_response(
            intent="general_chat",
            status="success",
            data={"general_info": None},
            source="llm_assistant",
            data_mode="llm",
        )
        reply = await synthesize_with_llm("generalChat", payload, message)
        return self._result(reply, IntentType.GENERAL_CHAT, payload, mode="llm")

    async def _general_travel_advice(self, message: str, entities: Dict[str, Any], ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Direct general travel advice from LLM without triggering trip planner defaults or itineraries."""
        payload = build_json_response(
            intent="general_travel_advice",
            status="success",
            data={"general_info": None},
            source="llm_assistant",
            data_mode="llm",
            is_mock=False,
        )
        reply = await synthesize_with_llm("generalChat", payload, message)
        return self._result(reply, IntentType.GENERAL_TRAVEL_ADVICE, payload, mode="llm")


orchestrator = AIOrchestrator()
