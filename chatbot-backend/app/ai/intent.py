import re
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List


class IntentType(str, Enum):
    TRAVEL_ITINERARY = "TRAVEL_ITINERARY"
    BUDGET_CALCULATION = "BUDGET_CALCULATION"
    FLIGHT_SEARCH = "FLIGHT_SEARCH"
    FLIGHT_STATUS = "FLIGHT_STATUS"
    HOTEL_SEARCH = "HOTEL_SEARCH"
    TRAIN_SEARCH = "TRAIN_SEARCH"
    TRAIN_STATUS = "TRAIN_STATUS"
    BUS_SEARCH = "BUS_SEARCH"
    BUS_STATUS = "BUS_STATUS"
    MAPS_ROUTE = "MAPS_ROUTE"
    WEATHER_INQUIRY = "WEATHER_INQUIRY"
    CAB_SEARCH = "CAB_SEARCH"
    DELAY_DISRUPTION = "DELAY_DISRUPTION"
    TRIP_MODIFICATION = "TRIP_MODIFICATION"
    PACKING_ASSISTANT = "PACKING_ASSISTANT"
    TRAVEL_CHECKLIST = "TRAVEL_CHECKLIST"
    PLACES_ACTIVITIES = "PLACES_ACTIVITIES"
    SHIPMENT_TRACKING = "SHIPMENT_TRACKING"
    SHIPMENT_REGISTER = "SHIPMENT_REGISTER"
    DRIVER_INFO = "DRIVER_INFO"
    VEHICLE_STATUS = "VEHICLE_STATUS"
    DELIVERY_HISTORY = "DELIVERY_HISTORY"
    SHIPMENT_STATUS = "SHIPMENT_STATUS"
    POLICY_RAG = "POLICY_RAG"
    TRAVELOGIX_INFORMATION = "TRAVELOGIX_INFORMATION"
    GENERAL_TRAVEL_ADVICE = "GENERAL_TRAVEL_ADVICE"
    GENERAL_CHAT = "GENERAL_CHAT"


KNOWN_INDIAN_DESTINATIONS = [
    "goa", "bangalore", "bengaluru", "mumbai", "delhi", "new delhi", "jaipur",
    "kerala", "munnar", "manali", "shimla", "agra", "varanasi", "chennai",
    "hyderabad", "kolkata", "udaipur", "rishikesh", "pondicherry", "puducherry",
    "ladakh", "leh", "kashmir", "srinagar", "darjeeling", "ooty", "coorg", "hampi",
    "pune", "ahmedabad", "chandigarh", "bhubaneswar", "kochi", "coimbatore",
    "mysore", "mysuru"
]

# Longest-first so multi-word names ("new delhi") win over their fragments ("delhi").
_KNOWN_DESTINATIONS_ORDERED = sorted(KNOWN_INDIAN_DESTINATIONS, key=len, reverse=True)

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "single": 1, "couple": 2, "few": 3, "weekend": 2
}

# --------------------------------------------------------------------------- #
# Stopwords
#
# Every token that can follow "to|in|for|visit|explore" (or precede "trip") in
# ordinary English is NOT a destination. Rejecting these in every destination
# branch is what stops "one person" -> "One" and "plan for me" -> "Me".
# --------------------------------------------------------------------------- #
PRONOUNS = {
    "i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "you", "your",
    "yours", "he", "she", "him", "her", "they", "them", "it", "this", "that",
    "these", "those", "someone", "somebody", "anyone", "anybody", "everyone",
}

VERBS = {
    "plan", "planning", "planned", "travel", "travelling", "traveling", "go",
    "going", "make", "making", "create", "creating", "explore", "exploring",
    "visit", "visiting", "help", "helping", "want", "wanna", "need", "needing",
    "book", "booking", "find", "finding", "search", "searching", "show",
    "showing", "give", "giving", "tell", "know", "like", "love", "build",
    "organise", "organize", "prepare", "arrange", "suggest", "recommend",
    "register", "send", "ship", "dispatch", "track", "know",
}

# Time / quantity nouns that read like places to the naive preposition extractor.
TIME_WORDS = {
    "day", "days", "night", "nights", "week", "weeks", "month", "months",
    "year", "years", "weekend", "weekends", "today", "tomorrow", "tonight",
    "morning", "afternoon", "evening", "night", "hour", "hours", "minute",
    "minutes", "time", "times", "date", "dates", "season", "summer", "winter",
    "monsoon", "spring", "autumn", "tonight", "weekday", "holiday", "holidays",
}

TRIP_NOUNS = {
    "trip", "trips", "tour", "tours", "vacation", "vacations", "itinerary",
    "itineraries", "travel", "journey", "holiday", "holidays", "plan", "plans",
    "schedule", "package", "packages", "booking", "bookings", "place", "places",
    "destination", "destinations", "city", "cities", "somewhere", "anywhere",
    "everywhere", "there", "here", "someplace", "somewhere", "abroad", "outstation",
}

ARTICLES = {"a", "an", "the", "some", "any", "no", "all", "each", "every"}

STOPWORD_EXTRA = {
    "please", "pls", "plz", "kindly", "can", "could", "would", "should", "will",
    "shall", "may", "might", "must", "do", "does", "did", "is", "are", "was",
    "were", "be", "been", "being", "am", "have", "has", "had", "and", "or",
    "but", "if", "of", "on", "at", "by", "with", "about", "into", "over",
    "under", "again", "then", "than", "so", "such", "very", "just", "also",
    "too", "only", "own", "same", "up", "down", "out", "off", "why", "how",
    "what", "when", "where", "which", "who", "whom", "whose", "yes", "no",
    "ok", "okay", "sure", "hey", "hi", "hello", "thanks", "thank", "you",
    "yourself", "us", "person", "people", "persons", "traveler", "traveller",
    "travelers", "travellers", "adult", "adults", "kid", "kids", "child",
    "children", "family", "friends", "friend", "group", "budget", "cost",
    "price", "prices", "rupees", "inr", "rs", "km", "kms", "kilometers",
    "kilometres", "miles", "status", "policy", "policies", "refund",
    "cancellation", "rules", "terms", "weather", "forecast", "temperature",
    "climate", "rain", "flights", "flight", "trains", "train", "buses", "bus",
    "hotels", "hotel", "resort", "resorts", "stay", "stays", "accommodation",
    "shipment", "shipments", "package", "packages", "parcel", "parcels",
    "courier", "freight", "cargo", "driver", "vehicle", "truck", "tracking",
    "number", "id", "code", "gate", "terminal", "seat", "seats", "available",
    "availability", "route", "distance", "far", "long", "much", "many", "more",
    "most", "less", "least", "between", "from", "to", "in", "for", "visit",
    "explore", "near", "nearest", "around", "nearby", "info", "information",
    "details", "detail", "recommendation", "recommendations", "suggestion",
    "suggestions", "option", "options", "list", "give", "need", "want",
    "should", "pack", "packing", "checklist", "first", "last", "next", "new",
    "good", "best", "great", "nice", "cheap", "cheapest", "affordable",
    "luxury", "budget", "deluxe", "star", "stars", "rating", "rated",
    "actually", "make", "change", "instead", "rather", "just", "please",
    "compromise", "compromises", "comfort", "comforts", "planning", "advice",
    "destination", "destinations", "travel", "travelling", "traveling",
    "vacation", "vacations", "family", "families", "elderly", "children",
    "child", "mistakes", "mistake", "priority", "priorities", "prioritize",
    "prioritise", "consider", "considering", "consideration", "considerations",
    "choose", "choosing", "choice", "choices", "inexpensive", "expensive",
    "holiday", "holidays", "parent", "parents", "activity", "activities",
    "now", "later", "well", "solo", "alone", "couple", "peaceful", "scenic",
    "popular", "famous", "top", "check", "checking", "before", "after", "during",
    "important", "importance",
}

# Number words are stopwords too ("a trip for one person" must not yield "One").
DEST_STOPWORDS = (
    set(NUMBER_WORDS.keys())
    | PRONOUNS
    | VERBS
    | TIME_WORDS
    | TRIP_NOUNS
    | ARTICLES
    | STOPWORD_EXTRA
)

# Pure greetings / acknowledgements carry no routing information.
GREETING_RE = re.compile(
    r"^(?:"
    r"hi|hello|hey|heya|yo|howdy|hola|namaste|greetings|good\s+(?:morning|afternoon|evening|day)"
    r"|thanks|thank\s+you|thx|ty|cheers|ok|okay|k|cool|great|nice|bye|goodbye|see\s+you"
    r")(?:[\s,.!?]*(?:there|buddy|mate|friend|sir|madam|ma'?am|everyone|all|travelogix|ai|bot|assistant))*"
    r"[\s,.!?]*$",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """
    Normalize text by lowercasing and standardizing common travel words and typos.
    """
    t = text.lower().strip()
    t = re.sub(r"\btravell?ogix\b|\btravel\s+logix\b", "travelogix", t)
    t = re.sub(r"\bplann?e?d?\b", "plan", t)
    t = re.sub(r"\bdayes?\b", "days", t)
    t = re.sub(r"\bitin[ea]r[ea]r?y\b", "itinerary", t)
    t = re.sub(r"\bclimate\b|\btemperature\b", "weather", t)

    # City typos
    t = re.sub(r"\bbanglore\b|\bbengaluru\b", "bangalore", t)
    t = re.sub(r"\bmysore\b|\bmysuru\b", "mysore", t)
    t = re.sub(r"\bhydrabad\b", "hyderabad", t)
    t = re.sub(r"\bchenai\b", "chennai", t)
    t = re.sub(r"\bnew\s+delhi\b|\bdelhi\b", "delhi", t)
    t = re.sub(r"\bgoa\b", "goa", t)
    t = re.sub(r"\bmumbai\b", "mumbai", t)

    # Travel & Logistics typos
    t = re.sub(r"\bshipmnt\b", "shipment", t)
    t = re.sub(r"\btrak\b|\btrack(?:ing|ed|s)?\b", "track", t)
    t = re.sub(r"\bfligt\b", "flight", t)
    t = re.sub(r"\bhotelss\b", "hotels", t)
    t = re.sub(r"\btrainss\b", "trains", t)
    t = re.sub(r"\bbuss\b", "bus", t)

    t = re.sub(r"\bshipm[ea]nt\b", "shipment", t)
    return t


def _word_re(term: str) -> re.Pattern:
    """Word-boundary matcher for a term ('days in' -> matches 'days in', not 'weekdaysin')."""
    return re.compile(rf"\b{re.escape(term)}\b")


def _has_any_word(text: str, words) -> bool:
    return any(_word_re(w).search(text) for w in words)


def _has_any_substring(text: str, needles) -> bool:
    return any(n in text for n in needles)


def is_plausible_destination(candidate: Optional[str]) -> bool:
    """
    Reject stopwords/verbs/number words/pronouns so a naive extractor can never
    return "One", "Me", "Plan", "Travel" or "Register" as a destination.
    """
    if not candidate:
        return False
    cleaned = candidate.strip().strip(".,!?;:'\"")
    if len(cleaned) < 3 or not re.fullmatch(r"[A-Za-z][A-Za-z\s'.-]*", cleaned):
        return False
    return cleaned.lower() not in DEST_STOPWORDS


def _pick_destination(candidates: List[Optional[str]]) -> Optional[str]:
    """Return the first candidate that is not a stopword/verb."""
    for cand in candidates:
        if is_plausible_destination(cand):
            return cand.strip().strip(".,!?;:'\"").capitalize()
    return None


def _known_destination(normalized: str, exclude: Optional[str] = None) -> Optional[str]:
    skip = (exclude or "").lower()
    for dest in _KNOWN_DESTINATIONS_ORDERED:
        if dest == skip:
            continue
        # If the known place is explicitly marked as origin or reference location (e.g. "from Bangalore", "near Bangalore", "starting from Bangalore"),
        # do not treat it as destination unless also marked as destination (e.g. "to Bangalore").
        if re.search(rf"\b(?:from|starting\s+from|departing\s+from|leaving\s+from|out\s+of|near|around|close\s+to|outside|by)\s+{re.escape(dest)}\b", normalized):
            if not re.search(rf"\b(?:to|visit|visiting|explore|exploring)\s+{re.escape(dest)}\b", normalized):
                continue

        if re.search(rf"\b{re.escape(dest)}\b", normalized):
            if dest in ["bangalore", "bengaluru"]:
                return "Bangalore"
            if dest in ["delhi", "new delhi"]:
                return "Delhi"
            return dest.title()
    return None


def extract_preference(text: str) -> Optional[str]:
    """Extract travel style/environment preference (e.g. hills, beaches, nature, heritage, relaxation)."""
    normalized = normalize_text(text)
    pref_map = {
        "hill": "hills",
        "hills": "hills",
        "mountain": "hills",
        "mountains": "hills",
        "hillstation": "hills",
        "hill station": "hills",
        "hill stations": "hills",
        "beach": "beaches",
        "beaches": "beaches",
        "coastal": "beaches",
        "sea": "beaches",
        "nature": "nature",
        "forest": "nature",
        "wildlife": "nature",
        "jungle": "nature",
        "heritage": "heritage",
        "historical": "heritage",
        "temple": "heritage",
        "temples": "heritage",
        "culture": "heritage",
        "adventure": "adventure",
        "trekking": "adventure",
        "relaxing": "relaxation",
        "relaxation": "relaxation",
        "peaceful": "relaxation",
    }
    for key, pref in pref_map.items():
        if re.search(rf"\b{re.escape(key)}\b", normalized):
            return pref
    return None


def extract_travellers_count(text: str) -> Optional[int]:
    """Extract number of travellers from various phrasing patterns."""
    normalized = normalize_text(text)

    if re.search(r"\b(?:alone|solo|myself|just me|by myself)\b", normalized):
        return 1

    match = re.search(r"(\d+)\s*(?:people|persons?|passengers?|travelers?|travellers?|guests?|members?)\b", normalized)
    if match:
        try:
            return max(1, min(30, int(match.group(1))))
        except ValueError:
            pass

    match = re.search(r"(\d+)\s+of\s+us\b", normalized)
    if match:
        try:
            return max(1, min(30, int(match.group(1))))
        except ValueError:
            pass

    if re.search(r"\b(?:couple|two of us)\b", normalized):
        return 2

    for word, val in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\s*(?:people|persons?|passengers?|travelers?|travellers?|guests?)\b", normalized) or re.search(rf"\b{word}\s+of\s+us\b", normalized):
            return val

    match = re.search(r"\b(?:we are|there are|with)\s+(\d+)\b", normalized)
    if match:
        try:
            return max(1, min(30, int(match.group(1))))
        except ValueError:
            pass

    return None



def extract_duration(text: str) -> Optional[int]:
    """Extract trip duration in days from various phrasing patterns."""
    normalized = normalize_text(text)

    match = re.search(r"(\d+)\s*[-]?\s*days?", normalized)
    if match:
        try:
            return max(1, min(30, int(match.group(1))))
        except ValueError:
            pass

    match = re.search(r"days?\s*[-]?\s*(\d+)", normalized)
    if match:
        try:
            return max(1, min(30, int(match.group(1))))
        except ValueError:
            pass

    for word, val in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\s*[-]?\s*days?\b", normalized) or re.search(rf"\bdays?\s*[-]?\s*{word}\b", normalized):
            return val

    if "week" in normalized:
        return 7
    if "weekend" in normalized:
        return 2

    return None



def extract_destination(text: str) -> Optional[str]:
    """
    Extract a travel destination city/state.

    Every branch rejects DEST_STOPWORDS candidates, so an unmatched phrase yields
    None (and the orchestrator can ask "Which city?") instead of a fabricated city.
    """
    normalized = normalize_text(text)

    # Origin guard: If text exclusively names an origin/reference location ("from Bangalore", "near Bangalore") without an explicit destination marker ("to Coorg"), return None.
    is_origin_phrase = bool(re.search(r"\b(?:from|starting\s+from|departing\s+from|leaving\s+from|out\s+of|near|around|close\s+to|outside)\s+[A-Za-z]", normalized))
    is_explicit_dest_phrase = bool(re.search(r"\b(?:visit|visiting|explore|exploring)\s+[A-Za-z]", normalized)) or bool(re.search(r"\bto\s+(?!(?:travel|go|fly|get|reach|book|take|do|plan|make|find|see)\b)[A-Za-z]", normalized))

    if is_origin_phrase and not is_explicit_dest_phrase:
        return None

    known = _known_destination(normalized)
    if known:
        return known

    candidates: List[Optional[str]] = []

    # "to Goa", "in Paris", "for Manali", "visit Hampi", "explore Coorg"
    for m in re.finditer(
        r"\b(?:to|in|for|visit|visiting|explore|exploring)\s+([A-Za-z][A-Za-z.-]*)",
        normalized,
    ):
        candidates.append(m.group(1))

    # "Goa trip", "Paris tour", "Manali itinerary"
    m = re.search(r"\b([A-Za-z][A-Za-z.-]*)\s+(?:trip|tour|itinerary|travel|vacation|holiday)\b", normalized)
    if m:
        candidates.append(m.group(1))

    # "days in Goa", "day in Paris"
    m = re.search(r"\bdays?\s+in\s+([A-Za-z][A-Za-z.-]*)", normalized)
    if m:
        candidates.append(m.group(1))

    picked = _pick_destination(candidates)
    if picked:
        return picked

    # Last resort: any leftover capitalised token that looks like a proper noun.
    for token in re.findall(r"\b([A-Z][a-z]{2,})\b", text or ""):
        if is_plausible_destination(token):
            return token
    return None


def _extract_place_after(text: str, prefix_pattern: str, exclude: Optional[str] = None) -> Optional[str]:
    """Return a plausible place name following `prefix_pattern` in the raw text."""
    match = re.search(prefix_pattern, text or "", re.IGNORECASE)
    if not match:
        return None
    candidate = match.group(1).strip().strip(".,!?;:'\"")
    if not candidate:
        return None
    # A naive capture can swallow a preposition ("Bangalore to") or an article
    # ("register a"); keep only the head noun phrase.
    candidate = re.split(r"\s+(?:to|from|for|in|at|on|and|then|under|with)\s+", candidate, flags=re.IGNORECASE)[0]
    candidate = re.sub(r"\s+(?:to|from|for|in|at|on|and|then|under|with)$", "", candidate, flags=re.IGNORECASE).strip()
    candidate = re.sub(r"\b(?:airport|station|junction|stand|beach|city)\b", "", candidate, flags=re.IGNORECASE).strip()
    candidate = re.sub(r"\s+\b(?:today|tomorrow|tonight|yesterday|now)\b$", "", candidate, flags=re.IGNORECASE).strip()
    # Drop a leading article ("a shipment", "the trip") before validating.
    candidate = re.sub(r"^(?:a|an|the|some|any)\s+", "", candidate, flags=re.IGNORECASE).strip()
    if not candidate:
        return None
    # The head word must itself look like a place and not like a verb/pronoun:
    # "register a" -> "register" is a verb, so the whole candidate is rejected.
    if not is_plausible_destination(candidate.split()[0]):
        return None
    if exclude and candidate.lower() == exclude.lower():
        return None
    if not is_plausible_destination(candidate):
        return None
    return candidate.title()


def extract_origin_destination(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract origin and destination from phrases like 'from Bangalore to Goa',
    'How far is Bangalore from Mysore?', 'Bangalore to Mysore by car', etc.
    """
    normalized = normalize_text(text)

    from_match = re.search(r"\b(?:from|near|around|close\s+to|outside)\s+([A-Za-z][A-Za-z.\-]*(?:\s+[A-Za-z][A-Za-z.\-]*)?)(?![A-Za-z])", normalized)
    to_match = re.search(r"\bto\s+([A-Za-z][A-Za-z.\-]*(?:\s+[A-Za-z][A-Za-z.\-]*)?)(?![A-Za-z])", normalized)

    orig_candidate = _extract_place_after(normalized, r"\b(?:from|near|around|close\s+to|outside)\s+([A-Za-z][A-Za-z.\-]*(?:\s+[A-Za-z][A-Za-z.\-]*)?)(?![A-Za-z])")
    dest_candidate = _extract_place_after(normalized, r"\bto\s+([A-Za-z][A-Za-z.\-]*(?:\s+[A-Za-z][A-Za-z.\-]*)?)(?![A-Za-z])")

    if orig_candidate and orig_candidate.lower() in DEST_STOPWORDS:
        orig_candidate = None
    if dest_candidate and dest_candidate.lower() in DEST_STOPWORDS:
        dest_candidate = None

    # Check for known destinations in text order
    found_known: List[Tuple[int, str]] = []
    for dest in _KNOWN_DESTINATIONS_ORDERED:
        for match in re.finditer(rf"\b{re.escape(dest)}\b", normalized):
            name = "Bangalore" if dest in ["bangalore", "bengaluru"] else dest.title()
            found_known.append((match.start(), name))

    found_known.sort(key=lambda x: x[0])

    unique_known: List[str] = []
    for pos, name in found_known:
        if not any(u.lower() == name.lower() for u in unique_known):
            unique_known.append(name)

    # If explicit "from X to Y" or "near X to Y"
    if from_match and to_match and from_match.start() < to_match.start():
        origin = orig_candidate or (unique_known[0] if len(unique_known) > 0 else None)
        destination = dest_candidate or (unique_known[1] if len(unique_known) > 1 else None)
        if origin and destination and origin.lower() != destination.lower():
            return origin, destination

    # If we have 2 known destinations, first mentioned is origin, second is destination
    if len(unique_known) >= 2:
        if to_match and from_match and to_match.start() < from_match.start():
            return unique_known[1], unique_known[0]
        return unique_known[0], unique_known[1]

    origin = orig_candidate
    destination = dest_candidate

    known_origin = _known_destination(normalized)
    if origin is None and re.search(r"\b(?:from|near|around|close\s+to|outside)\b", normalized):
        origin = known_origin

    if destination is None:
        destination = _known_destination(normalized, exclude=origin)

    if destination is None and origin is not None:
        destination = _extract_place_after(
            normalized,
            r"\bto\s+([A-Za-z][A-Za-z.\-]*(?:\s+[A-Za-z][A-Za-z.\-]*)?)(?![A-Za-z])",
            exclude=origin,
        )

    if origin is None and destination is None:
        return None, None

    if origin and destination and origin.lower() == destination.lower():
        destination = None

    return origin, destination


def extract_tracking_id(text: str) -> Optional[str]:
    """Extract full TLX tracking number from text dynamically."""
    if not text:
        return None

    # Pattern 1: Multi-part or hyphenated IDs e.g. TLX-2026-100001, TLX-8961AD64, TLX-DEMO-100001
    match = re.search(r"\b(TLX[-_]?[0-9A-Z]+(?:[-_][0-9A-Z]+)*)\b", text, re.IGNORECASE)
    if match:
        val = match.group(1).upper().replace("_", "-")
        if len(val) >= 5 and val != "TLX":
            return val

    # Pattern 2: Single string without hyphens e.g. TLX8961AD64, TLX2026100037
    match_single = re.search(r"\b(TLX[0-9A-Z]{5,20})\b", text, re.IGNORECASE)
    if match_single:
        return match_single.group(1).upper()

    # Pattern 3: Space-separated IDs e.g. TLX 2026 100001
    match_space = re.search(r"\b(TLX\s+[0-9A-Z]{2,10}(?:\s+[0-9A-Z]{2,10})*)\b", text, re.IGNORECASE)
    if match_space:
        return match_space.group(0).upper().replace(" ", "-")

    return None


def extract_flight_number(text: str) -> Optional[str]:
    """
    Extract an airline flight designator (AI 582, 6E-2041, QP1304).

    Returns None when the customer did not name a flight, so the orchestrator can
    ask for one instead of inventing a flight number.
    """
    normalized = normalize_text(text)
    match = re.search(r"\b([A-Z0-9]{2,3})\s*-?\s*(\d{3,4})\b", normalized.upper(), re.IGNORECASE)
    if not match:
        return None
    prefix, digits = match.group(1).upper(), match.group(2)
    if not re.search(r"[A-Z]", prefix):
        return None
    if prefix.lower() in DEST_STOPWORDS:
        return None
    return f"{prefix}-{digits}"


def extract_train_number(text: str) -> Optional[str]:
    """Extract a 4-5 digit Indian Railways train number, or a named train."""
    normalized = normalize_text(text)
    match = re.search(r"\b(\d{4,5})\b", normalized)
    if match:
        return match.group(1)
    named = re.search(r"\b([a-z]+(?:\s+[a-z]+)?\s+express)\b", normalized)
    if named:
        return named.group(1).title()
    return None


def extract_budget_amount(text: str) -> Optional[float]:
    """Extract budget amount e.g. 'under ₹35000', 'budget is ₹4,000', 'budget of 35000', '4000'."""
    match = re.search(r"(?:₹|rs\.?|inr|under|budget\s*(?:of|is|=)?)\s*(\d+[\d,.]*)", text, re.IGNORECASE)
    if match:
        try:
            val_str = match.group(1).replace(",", "")
            return float(val_str)
        except ValueError:
            pass
    return None



def has_word(text: str, word: str) -> bool:
    """Check if whole word exists in text using regex word boundary."""
    return bool(re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE))


def extract_travel_date(text: str) -> Optional[str]:
    """Extract requested date (today, tomorrow, or explicit date like 15 October)."""
    from datetime import datetime, timedelta, timezone
    normalized = normalize_text(text)
    now = datetime.now(timezone.utc)

    if has_word(normalized, "today"):
        return now.strftime("%Y-%m-%d")
    if has_word(normalized, "tomorrow"):
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    if "day after tomorrow" in normalized:
        return (now + timedelta(days=2)).strftime("%Y-%m-%d")

    # Pattern for "15 October", "15th Oct", "October 15", "15 Oct 2026"
    months = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
        "nov": 11, "november": 11, "dec": 12, "december": 12,
    }
    
    # Matches "15 October" or "15th Oct"
    m1 = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]+)(?:\s+(\d{4}))?\b", normalized)
    if m1:
        day_str, month_str, year_str = m1.group(1), m1.group(2).lower(), m1.group(3)
        if month_str in months:
            month_num = months[month_str]
            year_num = int(year_str) if year_str else now.year
            try:
                dt = datetime(year_num, month_num, int(day_str))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    # Matches "October 15"
    m2 = re.search(r"\b([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s+(\d{4}))?\b", normalized)
    if m2:
        month_str, day_str, year_str = m2.group(1).lower(), m2.group(2), m2.group(3)
        if month_str in months:
            month_num = months[month_str]
            year_num = int(year_str) if year_str else now.year
            try:
                dt = datetime(year_num, month_num, int(day_str))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    # ISO format YYYY-MM-DD
    m3 = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", normalized)
    if m3:
        return m3.group(1)

    return None



def _is_general_travel_advice(normalized: str, text: str) -> bool:
    """
    True if query asks for general travel advice, considerations, tips, mistakes,
    best times, destination suggestions, or planning guidelines without an explicit trip execution command.
    """
    advice_patterns = [
        r"what\s+should\s+i\s+consider",
        r"things?\s+to\s+consider",
        r"what\s+to\s+consider",
        r"what\s+are\s+some\s+(?:things?|tips?|mistakes?|destinations?|places?|hills?|beaches?|options?)",
        r"common\s+mistakes",
        r"mistakes\s+people\s+make",
        r"what\s+should\s+i\s+prioritize",
        r"what\s+to\s+prioritize",
        r"\bprioritize\b",
        r"\bprioritise\b",
        r"\bcompromise\b",
        r"save\s+money\s+(?:while|when|on)?\s*travel",
        r"important\s+to\s+check",
        r"check\s+before\s+booking",
        r"how\s+do\s+i\s+choose",
        r"choosing\s+a\s+(?:holiday|destination|hotel|flight|trip)",
        r"choose\s+the\s+right",
        r"travelling\s+with\s+(?:elderly|parents|children|kids|family|baby)",
        r"traveling\s+with\s+(?:elderly|parents|children|kids|family|baby)",
        r"what\s+should\s+i\s+pack",
        r"what\s+to\s+pack\s+for",
        r"what\s+should\s+i\s+look\s+for",
        r"tips\s+for\s+(?:planning|booking|choosing|travel)",
        r"advice\s+(?:on|for|before)",
        r"\b(?:suggest|recommend|recommendation|suggestions?)\s+(?:a\s+)?(?:destination|place|location|spot|trip)\b",
        r"\b(?:peaceful|hill|beach|scenic|best|popular)\s+(?:destinations?|places?|spots?|break)\b",
        r"\bdestinations?\s+(?:near|around|from|for)\b",
        r"\b(?:best|ideal|good)\s+time\s+to\s+visit\b",
        r"\bwhen\s+(?:is\s+the\s+best\s+time\s+to|should\s+i)\s+visit\b",
        r"\bfor\s+a\s+solo\s+trip\b",
        r"\bsolo\s+trip\b",
        r"\bcan\s+you\s+suggest\b",
        r"\bwhy\s+is\s+[a-z\s]+\s+(?:popular|famous|known|visited)\b",
        r"\bwhy\s+visit\b",
        r"\bsomewhere\s+(?:peaceful|scenic|quiet|relaxing)\b",
        r"\bshort\s+break\b",
        r"\bwhich\s+places\s+are\s+good\s+for\b",
        r"\bgood\s+for\s+(?:nature|family|solo|couples|parents|kids)\b",
        r"\bwhere\s+(?:can|should|could)\s+i\s+go\s+(?:with|for)\b",
    ]
    for pattern in advice_patterns:
        if re.search(pattern, normalized):
            if not re.search(r"\b(?:plan\s+(?:a|my|the|\d+)|visit\s+\w+\s+for|\d+\s*days?\s+in\s+[A-Za-z]|create\s+(?:a|an|\d+)|make\s+(?:a|an|\d+)|build\s+(?:a|an|\d+))\b", normalized):
                return True
    return False


def detect_intent(text: str) -> Tuple[IntentType, Dict[str, Any]]:
    """
    Classify customer intent and extract pertinent operational entities.
    Tolerates spelling mistakes, inverted word order, and casual phrasings.

    Never invents an entity: a missing destination/flight/train number stays absent
    so the orchestrator can ask a clarifying question.
    """
    normalized = normalize_text(text)
    entities: Dict[str, Any] = {}
    has_history_word = has_word(normalized, "history") or has_word(normalized, "shipments")

    # Check 0: Pure greetings / acknowledgements short-circuit.
    # "help me plan a trip" is NOT a greeting; only bare pleasantries match.
    if GREETING_RE.match(text.strip()) and not has_history_word:
        return IntentType.GENERAL_CHAT, entities

    # Check 0.3: General Travel Advice (before specific domain checks)
    if _is_general_travel_advice(normalized, text):
        orig, dest = extract_origin_destination(text)
        if dest and dest != orig:
            entities["destination"] = dest
        if orig:
            entities["origin"] = orig
        pref_val = extract_preference(text)
        if pref_val:
            entities["travel_preference"] = pref_val
        dur_val = extract_duration(text)
        if dur_val:
            entities["duration_days"] = dur_val
        return IntentType.GENERAL_TRAVEL_ADVICE, entities

    # Check 0.4: Policy RAG (takes precedence when policy is asked)
    if _has_any_word(normalized, ["policy", "policies", "cancellation", "refund", "terms", "rules"]):
        return IntentType.POLICY_RAG, entities

    # Check 0.5: Travelogix Platform & Company Information Questions
    if _has_any_substring(normalized, [
        "what is travelogix", "what is travel logix", "about travelogix",
        "how does travelogix work", "what services", "services does travelogix",
        "what travel services", "what logistics services", "who is travelogix",
        "tell me about travelogix", "travelogix platform", "travelogix features",
        "travelogix info", "travelogix background", "capabilities of travelogix",
    ]) or (
        has_word(normalized, "travelogix") and _has_any_word(normalized, ["what", "how", "who", "about", "info", "services", "work", "features", "capabilities"])
    ):
        return IntentType.TRAVELOGIX_INFORMATION, entities

    # Check 1: Shipment registration (before tracking keywords so that
    # "register a shipment" is not swallowed by the word "shipment").
    if _has_any_substring(normalized, [
        "register shipment", "register a shipment", "register a shipment",
        "send package", "send a package", "ship a package", "dispatch package",
    ]):
        orig, dest = extract_origin_destination(text)
        weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilo|kilos|kilogram)", normalized)
        entities["origin"] = orig
        entities["destination"] = dest
        entities["weight_kg"] = float(weight_match.group(1)) if weight_match else None
        entities["register_intent"] = True
        return IntentType.SHIPMENT_REGISTER, entities

    # Check 1.5: Driver & Vehicle status queries
    if _has_any_substring(normalized, ["driver assigned", "who is the driver", "driver status", "driver info", "driver phone"]):
        tracking_id = extract_tracking_id(text)
        entities["tracking_id"] = tracking_id
        return IntentType.DRIVER_INFO, entities

    if _has_any_substring(normalized, ["vehicle status", "show vehicle", "assigned vehicle", "vehicle number"]):
        tracking_id = extract_tracking_id(text)
        entities["tracking_id"] = tracking_id
        return IntentType.VEHICLE_STATUS, entities

    if _has_any_substring(normalized, ["book a cab", "cab from", "cab to", "taxi from", "taxi to", "airport cab", "cab fare"]):
        orig, dest = extract_origin_destination(text)
        entities["pickup"] = orig or extract_destination(text)
        entities["drop"] = dest
        return IntentType.CAB_SEARCH, entities

    # Check 2: Shipment tracking (explicit keywords or a TLX tracking id).
    tracking_id = extract_tracking_id(text)
    is_tracking_kw = _has_any_substring(normalized, [
        "where is my shipment", "track shipment", "track my shipment", "my shipments",
        "shipment history", "who is assigned to my shipment", "shipment status",
        "status of shipment", "show shipment", "show my shipment", "package status",
        "track my package", "track my parcel", "tracking number", "my package",
    ]) or has_history_word
    if tracking_id or is_tracking_kw:
        entities["tracking_id"] = tracking_id
        return IntentType.SHIPMENT_TRACKING, entities

    # Check 3: Weather Inquiry (if destination missing, _weather will ask which city).
    if _has_any_word(normalized, ["weather", "forecast", "climate", "rain", "sunny", "humidity"]):
        dest = extract_destination(text)
        if dest:
            entities["destination"] = dest
        return IntentType.WEATHER_INQUIRY, entities

    # Check 4: Flight status (must run before the bare "where is"/"track" keywords
    # and before generic flight search, which was shadowing it).
    quoted_flight = extract_flight_number(text)
    if (
        re.search(r"\bflight\s+status\b|\bstatus\s+of\s+(?:the\s+)?flight\b", normalized)
        or (has_word(normalized, "status") and has_word(normalized, "flight"))
        or (quoted_flight and has_word(normalized, "flight"))
        or (has_word(normalized, "flight") and _has_any_word(normalized, ["where", "gate", "boarding", "departure", "arrival", "delayed"]))
    ):
        if quoted_flight:
            entities["flight_number"] = quoted_flight
        return IntentType.FLIGHT_STATUS, entities

    # Check 5: Train status (makes the previously dead TRAIN_STATUS branch reachable).
    if (
        re.search(r"\btrain\s+status\b|\brunning\s+status\b|\btrain\s+running\b", normalized)
        or (has_word(normalized, "status") and has_word(normalized, "train"))
    ):
        train_number = extract_train_number(text)
        if train_number:
            entities["train_number"] = train_number
        return IntentType.TRAIN_STATUS, entities

    # Check 6: Bus status
    if re.search(r"\bbus\s+status\b|\bbus\s+tracking\b|\blive\s+bus\b", normalized) or (
        has_word(normalized, "status") and has_word(normalized, "bus")
    ):
        entities["bus_identifier"] = text.strip()
        return IntentType.BUS_STATUS, entities

    # Check 7: Disruption / Delay Planning
    if _has_any_substring(normalized, [
        "delayed by", "delay of", "delay by", "bus is delayed",
        "flight is delayed", "train is delayed", "what changes",
    ]):
        delay_match = re.search(r"(\d+)\s*hour", normalized)
        entities["delay_hours"] = float(delay_match.group(1)) if delay_match else 4.0
        dest = extract_destination(text)
        if dest:
            entities["destination"] = dest
        entities["duration_days"] = extract_duration(text)
        return IntentType.DELAY_DISRUPTION, entities

    # Check 7.5: Maps / Route Query (before generic transport searches so "Bangalore to Mysore by bus/car" matches MAPS_ROUTE)
    if _has_any_substring(normalized, [
        "how far", "how long", "distance from", "distance between", "distance to",
        "distance", "route to", "route from", "fastest route", "find a route",
        "cab fare", "directions to", "how do i get", "by car", "by drive", "by road", "by bus",
    ]):
        orig, dest = extract_origin_destination(text)
        if orig:
            entities["origin"] = orig
        if dest:
            entities["destination"] = dest
        if "by bus" in normalized or "bus" in normalized:
            entities["transport_mode"] = "bus"
        elif "by car" in normalized or "car" in normalized or "drive" in normalized:
            entities["transport_mode"] = "driving"
        return IntentType.MAPS_ROUTE, entities

    # Check 8: Transport searches
    if _has_any_word(normalized, ["flight", "flights", "fly", "airline", "airfare"]):
        orig, dest = extract_origin_destination(text)
        if orig:
            entities["origin"] = orig
        if dest:
            entities["destination"] = dest
        entities["travel_date"] = extract_travel_date(text)
        return IntentType.FLIGHT_SEARCH, entities


    if _has_any_word(normalized, ["train", "trains", "railway", "rail"]):
        orig, dest = extract_origin_destination(text)
        if orig:
            entities["origin"] = orig
        if dest:
            entities["destination"] = dest
        return IntentType.TRAIN_SEARCH, entities

    if _has_any_word(normalized, ["bus", "buses", "coach"]):
        orig, dest = extract_origin_destination(text)
        if orig:
            entities["origin"] = orig
        if dest:
            entities["destination"] = dest
        return IntentType.BUS_SEARCH, entities

    if _has_any_word(normalized, ["hotel", "hotels", "resort", "resorts", "stay", "accommodation", "hostel"]):
        dest = extract_destination(text)
        if dest:
            entities["location"] = dest
            entities["destination"] = dest
        max_p = extract_budget_amount(text)
        entities["max_price"] = int(max_p) if max_p else None
        return IntentType.HOTEL_SEARCH, entities

    # Check 9: Trip Modification
    if _has_any_substring(normalized, [
        "instead of", "change hotel", "replace flight", "add one more",
        "modify trip", "change trip",
    ]):
        dest = extract_destination(text)
        if dest:
            entities["destination"] = dest
        entities["duration_days"] = extract_duration(text)
        entities["modification_request"] = text
        return IntentType.TRIP_MODIFICATION, entities

    # Check 10: Packing Assistant & Travel Checklist
    if _has_any_substring(normalized, ["should i pack", "what to pack", "packing list", "packing suggestions"]):
        dest = extract_destination(text)
        if dest:
            entities["destination"] = dest
        entities["duration_days"] = extract_duration(text)
        return IntentType.PACKING_ASSISTANT, entities

    if _has_any_substring(normalized, ["travel checklist", "pre-travel checklist", "checklist for trip"]):
        return IntentType.TRAVEL_CHECKLIST, entities

    # Check 11: Budget Calculation (or budget constraint statement).
    budget_amt = extract_budget_amount(text)
    pref_val = extract_preference(text)
    dur_val = extract_duration(text)
    travellers_cnt = extract_travellers_count(text)
    orig_val, dest_from_od = extract_origin_destination(text)

    if budget_amt:
        entities["total_budget_inr"] = budget_amt
        entities["budget"] = budget_amt
    if pref_val:
        entities["travel_preference"] = pref_val
    if dur_val:
        entities["duration_days"] = dur_val
    if travellers_cnt is not None:
        entities["travelers_count"] = travellers_cnt
        entities["travellers"] = travellers_cnt
    if orig_val:
        entities["origin"] = orig_val

    if budget_amt and (
        _has_any_word(normalized, ["plan", "budget", "cost", "spend", "afford", "my"])
        or "budget is" in normalized
        or "budget of" in normalized
    ):
        dest = extract_destination(text)
        if dest:
            entities["destination"] = dest
        return IntentType.BUDGET_CALCULATION, entities

    # Check 13: Places & Activities
    if _has_any_substring(normalized, [
        "restaurant", "places to visit", "activities near", "things to do", "sightseeing",
    ]):
        dest = extract_destination(text)
        if dest:
            entities["location"] = dest
        return IntentType.PLACES_ACTIVITIES, entities

    # Check 14: Policy RAG
    if _has_any_word(normalized, [
        "policy", "policies", "cancellation", "refund", "terms", "rules",
    ]) or _has_any_substring(normalized, ["packaging rules", "allowed items", "shipment policy", "shipment policies", "delivery policy"]):
        return IntentType.POLICY_RAG, entities

    # Check 15: Travel Itinerary Generation & Trip Planning.
    # Require an explicit command to plan a trip or build an itinerary.
    explicit_plan_patterns = [
        r"\b(?:plan|planning|build|organise|organize|create|make|generate)\b.*?\b(?:trip|itinerary|tour|vacation|holiday|days?)\b",
        r"\bitinerary\s+for\b",
        r"\bplan\s+(?:the\s+)?trip\b",
        r"\bplan\s+(?:a\s+)?vacation\b",
        r"\bplan\s+itinerary\b",
        r"\bcreate\s+(?:an?\s+)?itinerary\b",
        r"\bmake\s+(?:an?\s+)?itinerary\b",
        r"\bplan\s+a\b",
        r"\bplan\s+my\b",
    ]
    has_explicit_plan_cmd = any(re.search(p, normalized) for p in explicit_plan_patterns) or (
        normalized.strip() in ["plan the trip", "plan it", "now plan the trip", "plan my trip", "plan the trip for me", "plan the trip for us"]
    )

    dest = dest_from_od or extract_destination(text)

    if has_explicit_plan_cmd:
        if dest:
            entities["destination"] = dest
        return IntentType.TRAVEL_ITINERARY, entities

    # If destination and duration both specified explicitly in prompt (e.g. "visit Coorg for 2 days"):
    if dest and dur_val and _has_any_word(normalized, ["visit", "go", "trip", "tour", "vacation"]):
        entities["destination"] = dest
        entities["duration_days"] = dur_val
        return IntentType.TRAVEL_ITINERARY, entities

    # If budget and plan word specified explicitly (e.g. "I have ₹7,000. Plan a trip from Bangalore"):
    if budget_amt and _has_any_word(normalized, ["plan", "itinerary", "build", "create"]):
        if dest:
            entities["destination"] = dest
        return IntentType.TRAVEL_ITINERARY, entities

    if dest:
        entities["destination"] = dest

    return IntentType.GENERAL_CHAT, entities


