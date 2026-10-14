"""
Customer-facing Text Presentation (JSON -> Markdown).

Converts internal JSON data structures into clean, friendly markdown responses.
Enforces the rule: NO internal metadata (provenance, travelogix_database (json),
is_mock, stack traces, debug variables) are ever shown to the customer.

Two shapes are produced:

* default (``compact=False``) - the full card view (one multi-line block per item),
  used by the admin/legacy surface;
* ``compact=True`` - the customer-chat view: at most ``limit`` items, ONE line per
  item, no booking links and no trailing footer, so an answer stays short. The
  ``max_items``/``limit`` argument caps how many rows are shown in either shape.
"""
from typing import Dict, Any, List, Optional


def _extract_inner_data(data: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        return data["data"]
    return data or {}


def _get_badge(data: Dict[str, Any], domain: str) -> str:
    prov = (data.get("provenance") or {}) if isinstance(data, dict) else {}
    data_mode = data.get("data_mode") or prov.get("mode")
    is_mock = data.get("is_mock") or prov.get("is_mock")

    if data_mode == "live" and not is_mock:
        return "Live data."
    elif data_mode in ("demo", "sample") or is_mock:
        return "*(Based on available travel data)*"
    return ""


def format_flights_response(
    data: Dict[str, Any],
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    compact: bool = False,
    limit: int = 4,
) -> str:
    if not data or not data.get("available", True) or data.get("status") in ("unavailable", "error"):
        msg = data.get("message") if isinstance(data, dict) and data.get("message") else "No flights found matching your search criteria."
        return f"### ✈️ Flight Search\n\n{msg}"

    inner = _extract_inner_data(data)
    results = inner.get("results") or inner.get("flights") or data.get("results") or data.get("flights") or []
    orig = inner.get("origin") or data.get("origin") or origin or "Origin"
    dest = inner.get("destination") or data.get("destination") or destination or "Destination"

    if not results:
        return f"### ✈️ Flights ({orig} → {dest})\n\nNo flights found matching your search criteria."

    lines = [f"### ✈️ Flights ({orig} → {dest})\n"]
    for idx, f in enumerate(results[: max(1, limit)], 1):
        num = f.get("flight_number", "N/A")
        airline = f.get("airline", "")
        dep = f.get("departure_time", "N/A")
        arr = f.get("arrival_time", "N/A")
        price = f.get("price") or f.get("price_inr") or 0
        curr = f.get("currency", "INR")
        dur = f.get("duration", "")
        stops = "Non-stop" if f.get("stops", 0) == 0 else f"{f.get('stops')} stop(s)"
        url = f.get("booking_url")
        money = f"₹{price:,.0f}" if curr == "INR" else f"{curr} {price:,.0f}"
        card_money = f"₹{price:,.0f} {curr}" if curr == "INR" else f"{curr} {price:,.0f}"
        label = f"{airline} ({num})" if airline else f"Flight {num}"

        if compact:
            lines.append(f"- **{label}** — {dep} → {arr} ({dur}, {stops}) · {money}")
            continue

        header = f"**{idx}. {label}**"
        lines.append(f"{header}")
        lines.append(f"   🕒 {dep} → {arr} ({dur} | {stops})")
        lines.append(f"   💰 {card_money}")
        if url:
            lines.append(f"   🔗 [Book Flight]({url})")
        lines.append("")

    if len(results) > limit:
        lines.append(f"_Showing {limit} of {len(results)} options — ask for more if you want the rest._")

    badge = _get_badge(data, "flight")
    if badge and not compact:
        lines.append(badge)

    return "\n".join(lines).strip()


def format_hotels_response(
    data: Dict[str, Any],
    city: Optional[str] = None,
    compact: bool = False,
    limit: int = 4,
) -> str:
    inner = _extract_inner_data(data)
    location = inner.get("city") or data.get("city") or inner.get("location") or data.get("location") or city or "Requested City"

    if not data or not data.get("available", True) or data.get("status") in ("unavailable", "error"):
        return f"### 🏨 Hotels in {location}\n\nNo hotels found matching your search criteria."

    results = inner.get("results") or inner.get("hotels") or data.get("results") or data.get("hotels") or []

    if not results:
        return f"### 🏨 Hotels in {location}\n\nNo hotels found matching your search criteria."

    lines = [f"### 🏨 Recommended Stays in {location}\n"]
    for idx, h in enumerate(results[: max(1, limit)], 1):
        name = h.get("hotel_name", "N/A")
        rating = h.get("rating", 4.0)
        price = h.get("price_per_night", 0)
        room = h.get("room_type", "Deluxe Room")
        url = h.get("hotel_url")

        if compact:
            lines.append(f"- **{name}** ⭐ {rating} — {room} · ₹{price:,.0f}/night")
            continue

        lines.append(f"**{idx}. {name}** ⭐ {rating}")
        lines.append(f"   🛏️ {room}")
        lines.append(f"   💰 ₹{price:,.0f} / night")
        if url:
            lines.append(f"   🔗 [View & Book]({url})")
        lines.append("")

    if len(results) > limit:
        lines.append(f"_Showing {limit} of {len(results)} stays._")

    badge = _get_badge(data, "hotel")
    if badge and not compact:
        lines.append(badge)

    return "\n".join(lines).strip()


def format_trains_response(
    data: Dict[str, Any],
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    compact: bool = False,
    limit: int = 4,
) -> str:
    if not data or not data.get("available", True) or data.get("status") in ("unavailable", "error"):
        return "### 🚆 Train Search\n\nNo train schedules found for this route."

    inner = _extract_inner_data(data)
    results = inner.get("results") or inner.get("trains") or data.get("results") or data.get("trains") or []
    orig = inner.get("origin") or data.get("origin") or origin or "Origin"
    dest = inner.get("destination") or data.get("destination") or destination or "Destination"

    if not results:
        return f"### 🚆 Trains ({orig} → {dest})\n\nNo train schedules found for this route."

    lines = [f"### 🚆 Train Schedules ({orig} → {dest})\n"]
    for idx, t in enumerate(results[: max(1, limit)], 1):
        num = t.get("train_number", "N/A")
        name = t.get("train_name", "Express")
        dep = t.get("departure", "N/A")
        arr = t.get("arrival", "N/A")
        fare = t.get("fare", 0)
        classes = t.get("available_classes") or t.get("classes") or []
        url = t.get("provider_url")

        if compact:
            suffix = f" · {', '.join(map(str, classes))}" if classes else ""
            lines.append(f"- **{name}** ({num}) — {dep} → {arr} · ₹{fare:,.0f}{suffix}")
            continue

        lines.append(f"**{idx}. {name} ({num})**")
        lines.append(f"   🕒 {dep} → {arr}")
        lines.append(f"   💰 ₹{fare:,.0f}")
        if url:
            lines.append(f"   🔗 [Book Train]({url})")
        lines.append("")

    if len(results) > limit:
        lines.append(f"_Showing {limit} of {len(results)} trains._")

    badge = _get_badge(data, "train")
    if badge and not compact:
        lines.append(badge)

    return "\n".join(lines).strip()


def format_buses_response(
    data: Dict[str, Any],
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    compact: bool = False,
    limit: int = 4,
) -> str:
    if not data or not data.get("available", True) or data.get("status") in ("unavailable", "error"):
        return "### 🚌 Bus Search\n\nNo bus options found for this route."

    inner = _extract_inner_data(data)
    results = inner.get("results") or inner.get("buses") or data.get("results") or data.get("buses") or []
    orig = inner.get("origin") or data.get("origin") or origin or "Origin"
    dest = inner.get("destination") or data.get("destination") or destination or "Destination"

    if not results:
        return f"### 🚌 Buses ({orig} → {dest})\n\nNo bus options found for this route."

    lines = [f"### 🚌 Bus Options ({orig} → {dest})\n"]
    for idx, b in enumerate(results[: max(1, limit)], 1):
        op = b.get("operator", "Express Bus")
        btype = b.get("bus_type", "AC Sleeper")
        dep = b.get("departure", "N/A")
        arr = b.get("arrival", "N/A")
        fare = b.get("fare", 0)
        url = b.get("booking_url")

        if compact:
            lines.append(f"- **{op}** — {dep} → {arr} ({btype}) · ₹{fare:,.0f}")
            continue

        lines.append(f"**{idx}. {op} ({btype})**")
        lines.append(f"   🕒 {dep} → {arr}")
        lines.append(f"   💰 ₹{fare:,.0f}")
        if url:
            lines.append(f"   🔗 [Book Bus]({url})")
        lines.append("")

    if len(results) > limit:
        lines.append(f"_Showing {limit} of {len(results)} buses._")

    badge = _get_badge(data, "bus")
    if badge and not compact:
        lines.append(badge)

    return "\n".join(lines).strip()


def format_weather_response(
    data: Dict[str, Any],
    city: Optional[str] = None,
    compact: bool = False,
) -> str:
    if not data or not data.get("available", True) or data.get("status") in ("unavailable", "error"):
        return "### 🌤️ Weather Forecast\n\nWeather information for this location is currently unavailable."

    inner = _extract_inner_data(data)
    c = inner.get("city") or data.get("city") or inner.get("location") or data.get("location") or city or "Requested Location"
    temp = inner.get("temperature") or inner.get("temperature_range") or "25°C"
    feels = inner.get("feels_like", temp)
    temp_range = inner.get("temperature_range") or data.get("temperature_range")
    cond = inner.get("condition", "Clear")
    hum = inner.get("humidity", "60%")
    precip = inner.get("precipitation_chance")
    clothing = inner.get("clothing_recommendation")

    if compact:
        # A static seasonal reference is better described by its range than by a
        # single "current" number, which would imply a live reading.
        shown_temp = temp_range or (temp if isinstance(temp, str) else f"{temp}°C")
        parts = [f"**{c}:** {cond}", shown_temp,
                 f"humidity {hum}" if isinstance(hum, str) else f"humidity {hum}%"]
        if precip:
            parts.append(f"rain {precip}")
        line = " · ".join(parts)
        if clothing:
            line += f"\n{clothing}"
        return line

    lines = [
        f"### 🌤️ Weather in {c}\n",
        f"**Condition**: {cond}",
        f"**Temperature**: {temp}" if isinstance(temp, str) else f"**Temperature**: {temp}°C (Feels like {feels}°C)",
        f"**Humidity**: {hum}" if isinstance(hum, str) else f"**Humidity**: {hum}%",
    ]
    if clothing:
        lines.append(f"**Recommendation**: {clothing}")

    badge = _get_badge(data, "weather")
    if badge:
        lines.append(f"\n{badge}")

    return "\n".join(lines)


def format_route_response(
    data: Dict[str, Any],
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    compact: bool = False,
) -> str:
    if not data or not data.get("available", True) or data.get("status") in ("unavailable", "error"):
        return "Distance and duration information for this route is currently unavailable."

    inner = _extract_inner_data(data)
    orig = inner.get("origin") or data.get("origin") or origin or "Origin"
    dest = inner.get("destination") or data.get("destination") or destination or "Destination"
    dist = inner.get("road_distance_estimate_km") or inner.get("distance_km") or inner.get("distance") or "N/A"
    if isinstance(dist, (int, float)):
        dist = f"{dist} km"
    dur = inner.get("duration_formatted") or inner.get("duration") or "N/A"
    route_name = inner.get("route") or inner.get("recommended_route")
    maps_url = inner.get("maps_url")
    fare = inner.get("cab_fare_estimate_inr")

    if dist == "N/A" or dur == "N/A":
        return "Distance and duration information for this route is currently unavailable."

    if compact:
        line = f"**{orig} → {dest}:** {dist}, about {dur}"
        if fare:
            line += f" · cab ≈ ₹{fare:,.0f}"
        return line

    lines = [
        f"### 🗺️ {orig} → {dest}\n",
        f"📍 Distance: {dist}",
        f"⏱️ Estimated time: {dur}",
    ]
    if route_name and route_name not in ("N/A", "Primary Route"):
        lines.append(f"\n🛣️ Route: {route_name}")
    if maps_url:
        lines.append(f"🔗 [View on Google Maps]({maps_url})")

    badge = _get_badge(data, "route")
    if badge:
        lines.append(f"\n{badge}")

    return "\n".join(lines)


def format_cabs_response(data: Dict[str, Any], pickup: Optional[str] = None, drop: Optional[str] = None) -> str:
    if not data or not data.get("available", True) or data.get("status") in ("unavailable", "error"):
        return "### 🚖 Cab Estimation\n\nLive cab estimation data is currently unavailable, and no sample data is available."

    inner = _extract_inner_data(data)
    p = inner.get("pickup") or data.get("pickup") or pickup or "Pickup Point"
    d = inner.get("drop") or data.get("drop") or drop or "Destination"
    results = inner.get("results") or inner.get("cabs") or data.get("results") or data.get("cabs") or []

    if not results:
        # No cab rows were supplied: never invent a fare.
        return (
            f"### 🚖 Cab Options ({p} → {d})\n\n"
            "No cab estimates are available for this route."
        )

    lines = [f"### 🚖 Cab Options ({p} → {d})\n"]
    for idx, c in enumerate(results, 1):
        vtype = c.get("vehicle_type", "Sedan")
        fare = c.get("estimated_fare", 500)
        eta = c.get("estimated_time", "10 mins")
        url = c.get("booking_url")
        lines.append(f"**{idx}. TravelLogix {vtype}**")
        lines.append(f"   🕒 Pickup in {eta}")
        lines.append(f"   💰 Est. Fare: ₹{fare:,.0f}")
        if url:
            lines.append(f"   🔗 [Book Cab]({url})")
        lines.append("")

    return "\n".join(lines).strip()
