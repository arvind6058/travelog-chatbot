"""
Conversation Context & Slot Preservation Manager.

Maintains active intent and slot state across conversation turns so follow-up
questions ("tomorrow", "under 5000", "2 passengers") seamlessly resume JSON intent execution.
"""
from typing import Dict, Any, Optional
from app.ai.intent import (
    IntentType,
    detect_intent,
    extract_origin_destination,
    extract_destination,
    extract_travel_date,
    extract_budget_amount,
    extract_tracking_id,
    extract_flight_number,
    extract_train_number,
)


class ConversationSession:
    """Stores pending intent and collected slots for a conversation across turns."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.pending_intent: Optional[IntentType] = None
        self.slots: Dict[str, Any] = {}

    def set_pending(self, intent: IntentType, slots: Dict[str, Any]):
        self.pending_intent = intent
        for k, v in slots.items():
            if v is not None:
                self.slots[k] = v

    def update_slots(self, new_slots: Dict[str, Any]):
        for k, v in new_slots.items():
            if v is not None:
                self.slots[k] = v

    def get_all_slots(self, entities: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Merge stored session slots with current turn entities (current turn has priority)."""
        merged = dict(self.slots)
        if entities:
            for k, v in entities.items():
                if v is not None:
                    merged[k] = v
        return merged

    def clear_pending(self):
        """Clear only the pending intent while retaining saved slot context across turns."""
        self.pending_intent = None

    def clear(self):
        """Fully reset session state (e.g. for hard session resets)."""
        self.pending_intent = None
        self.slots.clear()


_SESSION_STORE: Dict[str, ConversationSession] = {}


def get_conversation_session(conversation_id: Optional[str] = None, user_id: Optional[str] = None) -> ConversationSession:
    if conversation_id is None and user_id is None:
        return ConversationSession("default_session")
    key = conversation_id or user_id
    if key not in _SESSION_STORE:
        _SESSION_STORE[key] = ConversationSession(key)
    return _SESSION_STORE[key]



def try_resolve_follow_up(
    message: str,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Optional[tuple[IntentType, Dict[str, Any]]]:
    """
    If there is a pending intent in session and message provides missing slot value
    (e.g., date, budget, passengers, travellers, destination, origin, duration, preference), return resolved (IntentType, merged_entities).
    """
    session = get_conversation_session(conversation_id, user_id)
    if not session.pending_intent:
        return None

    from app.ai.intent import (
        extract_duration,
        extract_preference,
        extract_travellers_count,
    )

    new_intent, _ = detect_intent(message)
    if new_intent in (IntentType.GENERAL_TRAVEL_ADVICE, IntentType.POLICY_RAG, IntentType.TRAVELOGIX_INFORMATION):
        return None

    # Trip planning intents transition smoothly without clearing stored slots
    trip_intents = (IntentType.TRAVEL_ITINERARY, IntentType.BUDGET_CALCULATION, IntentType.PLACES_ACTIVITIES)
    if new_intent not in (IntentType.GENERAL_CHAT, session.pending_intent) and new_intent not in trip_intents:
        session.clear_pending()
        return None

    pending_intent = session.pending_intent
    merged_slots = dict(session.slots)

    date_val = extract_travel_date(message)
    budget_val = extract_budget_amount(message)
    orig_val, dest_val = extract_origin_destination(message)
    # Only fallback to extract_destination if message does NOT contain an origin marker ("from ")
    import re
    if not dest_val and not (orig_val and re.search(r"\b(?:from|starting\s+from|departing\s+from|leaving\s+from|out\s+of)\b", message, re.IGNORECASE)):
        dest_val = extract_destination(message)

    tracking_val = extract_tracking_id(message)
    dur_val = extract_duration(message)
    pref_val = extract_preference(message)
    travellers_cnt = extract_travellers_count(message)

    room_match = re.search(r"(\d+)\s*rooms?", message, re.IGNORECASE)
    room_count = int(room_match.group(1)) if room_match else None

    has_new_slot = False

    if orig_val is not None:
        merged_slots["origin"] = orig_val
        has_new_slot = True

    if dest_val is not None:
        merged_slots["destination"] = dest_val
        has_new_slot = True

    if dur_val is not None:
        merged_slots["duration_days"] = dur_val
        has_new_slot = True

    if budget_val is not None:
        merged_slots["total_budget_inr"] = budget_val
        merged_slots["budget"] = budget_val
        has_new_slot = True

    if pref_val is not None:
        merged_slots["travel_preference"] = pref_val
        has_new_slot = True

    if travellers_cnt is not None:
        merged_slots["travelers_count"] = travellers_cnt
        merged_slots["travellers"] = travellers_cnt
        has_new_slot = True

    if pending_intent in (IntentType.FLIGHT_SEARCH, IntentType.TRAIN_SEARCH, IntentType.BUS_SEARCH):
        if date_val and not merged_slots.get("travel_date"):
            merged_slots["travel_date"] = date_val
            has_new_slot = True

    elif pending_intent == IntentType.HOTEL_SEARCH:
        if date_val and not merged_slots.get("check_in"):
            merged_slots["check_in"] = date_val
            has_new_slot = True
        if room_count and not merged_slots.get("rooms"):
            merged_slots["rooms"] = room_count
            has_new_slot = True

    elif pending_intent == IntentType.SHIPMENT_TRACKING:
        if tracking_val and not merged_slots.get("tracking_id"):
            merged_slots["tracking_id"] = tracking_val
            has_new_slot = True

    if has_new_slot or (session.pending_intent and (merged_slots.get("travel_date") or merged_slots.get("destination") or merged_slots.get("origin") or merged_slots.get("max_price") or merged_slots.get("tracking_id") or merged_slots.get("duration_days") or merged_slots.get("travel_preference") or merged_slots.get("travelers_count"))):
        session.slots = merged_slots
        return pending_intent, merged_slots

    return None


