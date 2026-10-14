"""
One-shot generator for the TravelLogix JSON travel datasets.

Run:  python scripts/generate_travel_json.py

Deterministic (fixed seed): re-running produces byte-identical files, so the
dataset can be regenerated and reviewed with git diff.

Coverage: every city below gets flights (both directions), hotels, weather and
ground transport (trains/buses) on realistic Indian corridors. Values are
plausible reference data for demo/offline mode - the app labels them as such.

The original hand-curated rows that existing tests/UI reference
(BLR->DEL AI-101 / 6E-2041 / AI-205 / UK-812, BOM->DEL 6E-5321 / AI-665,
BLR->GOI 6E-382 / I5-1324, MAA->BLR 6E-441, and the Goa/Bangalore/Delhi/Mumbai
hotels) are preserved verbatim and merged in.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"

# --------------------------------------------------------------------------- #
# City reference data: (city name, IATA, lat, lon, state/region label)
# --------------------------------------------------------------------------- #
CITIES: Dict[str, Dict[str, Any]] = {
    "Bangalore": {"iata": "BLR", "lat": 12.9716, "lon": 77.5946, "region": "Karnataka"},
    "Delhi": {"iata": "DEL", "lat": 28.6139, "lon": 77.2090, "region": "Delhi NCR"},
    "Mumbai": {"iata": "BOM", "lat": 19.0760, "lon": 72.8777, "region": "Maharashtra"},
    "Chennai": {"iata": "MAA", "lat": 13.0827, "lon": 80.2707, "region": "Tamil Nadu"},
    "Hyderabad": {"iata": "HYD", "lat": 17.3850, "lon": 78.4867, "region": "Telangana"},
    "Kolkata": {"iata": "CCU", "lat": 22.5726, "lon": 88.3639, "region": "West Bengal"},
    "Pune": {"iata": "PNQ", "lat": 18.5204, "lon": 73.8567, "region": "Maharashtra"},
    "Goa": {"iata": "GOI", "lat": 15.2993, "lon": 74.1240, "region": "Goa"},
    "Jaipur": {"iata": "JAI", "lat": 26.9124, "lon": 75.7873, "region": "Rajasthan"},
    "Kochi": {"iata": "COK", "lat": 9.9312, "lon": 76.2673, "region": "Kerala"},
    "Mysore": {"iata": "MYQ", "lat": 12.2958, "lon": 76.6394, "region": "Karnataka"},
    "Ooty": {"iata": "UDR", "lat": 11.4102, "lon": 76.6950, "region": "Tamil Nadu"},
    "Coorg": {"iata": "CNN", "lat": 12.3375, "lon": 75.8069, "region": "Karnataka"},
    "Hampi": {"iata": "HGI", "lat": 15.3350, "lon": 76.4600, "region": "Karnataka"},
    "Manali": {"iata": "KUU", "lat": 32.2432, "lon": 77.1892, "region": "Himachal Pradesh"},
    "Shimla": {"iata": "SLV", "lat": 31.1048, "lon": 77.1734, "region": "Himachal Pradesh"},
    "Udaipur": {"iata": "UDR", "lat": 24.5854, "lon": 73.7125, "region": "Rajasthan"},
    "Varanasi": {"iata": "VNS", "lat": 25.3176, "lon": 82.9739, "region": "Uttar Pradesh"},
    "Agra": {"iata": "AGR", "lat": 27.1767, "lon": 78.0081, "region": "Uttar Pradesh"},
    "Rishikesh": {"iata": "DED", "lat": 30.0869, "lon": 78.2676, "region": "Uttarakhand"},
    "Pondicherry": {"iata": "PNY", "lat": 11.9416, "lon": 79.8083, "region": "Tamil Nadu"},
    "Tirupati": {"iata": "TIR", "lat": 13.6288, "lon": 79.4192, "region": "Andhra Pradesh"},
    "Madurai": {"iata": "IXM", "lat": 9.9252, "lon": 78.1198, "region": "Tamil Nadu"},
    "Coimbatore": {"iata": "CJB", "lat": 11.0168, "lon": 76.9558, "region": "Tamil Nadu"},
    "Trivandrum": {"iata": "TRV", "lat": 8.5241, "lon": 76.9366, "region": "Kerala"},
    "Mangalore": {"iata": "IXE", "lat": 12.9141, "lon": 74.8560, "region": "Karnataka"},
    "Gokarna": {"iata": "IXG", "lat": 14.5479, "lon": 74.3188, "region": "Karnataka"},
    "Wayanad": {"iata": "CCJ", "lat": 11.6854, "lon": 76.1320, "region": "Kerala"},
    "Chikmagalur": {"iata": "IXE", "lat": 13.3161, "lon": 75.7720, "region": "Karnataka"},
    "Darjeeling": {"iata": "IXB", "lat": 27.0360, "lon": 88.2627, "region": "West Bengal"},
    "Amritsar": {"iata": "ATQ", "lat": 31.6340, "lon": 74.8723, "region": "Punjab"},
    "Ahmedabad": {"iata": "AMD", "lat": 23.0225, "lon": 72.5714, "region": "Gujarat"},
}

# --------------------------------------------------------------------------- #
# Airline reference: (name, IATA designator, booking host, price factor)
# --------------------------------------------------------------------------- #
AIRLINES: List[Tuple[str, str, str, float]] = [
    ("IndiGo", "6E", "https://www.goindigo.in", 0.92),
    ("Air India", "AI", "https://www.airindia.com", 1.06),
    ("Vistara", "UK", "https://www.airvistara.com", 1.14),
    ("Air India Express", "IX", "https://www.airindiaexpress.com", 0.96),
    ("Akasa Air", "QP", "https://www.akasaair.com", 0.94),
    ("SpiceJet", "SG", "https://www.spicejet.com", 0.90),
    ("AirAsia India", "I5", "https://www.airasia.com", 0.89),
    ("Alliance Air", "9I", "https://www.airindia.com", 1.00),
    ("Star Air", "S5", "https://www.starair.in", 1.02),
]

# Pairs that already exist by hand. Kept exactly, so nothing downstream breaks.
PRESERVED_FLIGHTS: List[Dict[str, Any]] = [
    {"flight_number": "AI-101", "airline": "Air India", "airline_code": "AI", "origin": "Bangalore", "destination": "Delhi",
     "departure_time": "06:15 AM", "arrival_time": "08:55 AM", "duration": "2h 40m", "stops": 0, "type": "Non-stop",
     "price": 4850, "price_inr": 4850, "currency": "INR", "booking_url": "https://www.airindia.com"},
    {"flight_number": "6E-2041", "airline": "IndiGo", "airline_code": "6E", "origin": "Bangalore", "destination": "Delhi",
     "departure_time": "08:30 AM", "arrival_time": "11:15 AM", "duration": "2h 45m", "stops": 0, "type": "Non-stop",
     "price": 5100, "price_inr": 5100, "currency": "INR", "booking_url": "https://www.goindigo.in"},
    {"flight_number": "AI-205", "airline": "Air India", "airline_code": "AI", "origin": "Bangalore", "destination": "Delhi",
     "departure_time": "10:20 AM", "arrival_time": "01:05 PM", "duration": "2h 45m", "stops": 1, "type": "1 stop",
     "price": 5240, "price_inr": 5240, "currency": "INR", "booking_url": "https://www.airindia.com"},
    {"flight_number": "UK-812", "airline": "Vistara", "airline_code": "UK", "origin": "Bangalore", "destination": "Delhi",
     "departure_time": "05:30 PM", "arrival_time": "08:15 PM", "duration": "2h 45m", "stops": 0, "type": "Non-stop",
     "price": 6100, "price_inr": 6100, "currency": "INR", "booking_url": "https://www.airvistara.com"},
    {"flight_number": "6E-5321", "airline": "IndiGo", "airline_code": "6E", "origin": "Mumbai", "destination": "Delhi",
     "departure_time": "07:00 AM", "arrival_time": "09:10 AM", "duration": "2h 10m", "stops": 0, "type": "Non-stop",
     "price": 4200, "price_inr": 4200, "currency": "INR", "booking_url": "https://www.goindigo.in"},
    {"flight_number": "AI-665", "airline": "Air India", "airline_code": "AI", "origin": "Mumbai", "destination": "Delhi",
     "departure_time": "11:30 AM", "arrival_time": "01:45 PM", "duration": "2h 15m", "stops": 0, "type": "Non-stop",
     "price": 4650, "price_inr": 4650, "currency": "INR", "booking_url": "https://www.airindia.com"},
    {"flight_number": "6E-382", "airline": "IndiGo", "airline_code": "6E", "origin": "Bangalore", "destination": "Goa",
     "departure_time": "08:10 AM", "arrival_time": "09:25 AM", "duration": "1h 15m", "stops": 0, "type": "Non-stop",
     "price": 3200, "price_inr": 3200, "currency": "INR", "booking_url": "https://www.goindigo.in"},
    {"flight_number": "I5-1324", "airline": "AirAsia India", "airline_code": "I5", "origin": "Bangalore", "destination": "Goa",
     "departure_time": "02:40 PM", "arrival_time": "03:55 PM", "duration": "1h 15m", "stops": 0, "type": "Non-stop",
     "price": 2950, "price_inr": 2950, "currency": "INR", "booking_url": "https://www.airasia.com"},
    {"flight_number": "6E-441", "airline": "IndiGo", "airline_code": "6E", "origin": "Chennai", "destination": "Bangalore",
     "departure_time": "09:15 AM", "arrival_time": "10:15 AM", "duration": "1h 00m", "stops": 0, "type": "Non-stop",
     "price": 2400, "price_inr": 2400, "currency": "INR", "booking_url": "https://www.goindigo.in"},
]

# --------------------------------------------------------------------------- #
# Route network: each hub connects to these destinations (undirected).
# --------------------------------------------------------------------------- #
ROUTE_NETWORK: Dict[str, List[str]] = {
    "Bangalore": ["Delhi", "Mumbai", "Goa", "Chennai", "Hyderabad", "Kolkata", "Pune", "Kochi", "Jaipur",
                  "Mangalore", "Coimbatore", "Trivandrum", "Madurai", "Tirupati", "Varanasi", "Ahmedabad",
                  "Amritsar", "Udaipur", "Pondicherry", "Gokarna", "Mysore", "Hampi"],
    "Delhi": ["Mumbai", "Goa", "Chennai", "Hyderabad", "Kolkata", "Pune", "Kochi", "Jaipur", "Varanasi",
              "Agra", "Rishikesh", "Manali", "Shimla", "Udaipur", "Amritsar", "Ahmedabad", "Darjeeling",
              "Trivandrum", "Madurai", "Coimbatore", "Tirupati", "Mangalore"],
    "Mumbai": ["Goa", "Chennai", "Hyderabad", "Kolkata", "Pune", "Kochi", "Jaipur", "Ahmedabad", "Udaipur",
               "Varanasi", "Delhi", "Bangalore", "Coimbatore", "Trivandrum", "Mangalore", "Gokarna",
               "Amritsar", "Agra", "Tirupati", "Madurai"],
    "Chennai": ["Hyderabad", "Kolkata", "Goa", "Kochi", "Coimbatore", "Madurai", "Tirupati", "Pondicherry",
                "Trivandrum", "Mangalore", "Varanasi", "Jaipur"],
    "Hyderabad": ["Kolkata", "Goa", "Pune", "Kochi", "Jaipur", "Varanasi", "Tirupati", "Ahmedabad",
                  "Coimbatore", "Madurai", "Udaipur", "Amritsar"],
    "Kolkata": ["Goa", "Kochi", "Jaipur", "Varanasi", "Darjeeling", "Agra", "Ahmedabad", "Pune",
                "Trivandrum", "Amritsar"],
    "Pune": ["Goa", "Kochi", "Jaipur", "Ahmedabad", "Udaipur", "Varanasi", "Hyderabad", "Mangalore"],
    "Goa": ["Kochi", "Mangalore", "Gokarna", "Jaipur", "Ahmedabad", "Trivandrum", "Hyderabad", "Pune",
            "Udaipur", "Amritsar"],
    "Jaipur": ["Udaipur", "Varanasi", "Agra", "Ahmedabad", "Amritsar", "Kochi", "Darjeeling", "Manali"],
    "Kochi": ["Trivandrum", "Mangalore", "Coimbatore", "Madurai", "Wayanad", "Gokarna", "Ahmedabad"],
    "Varanasi": ["Agra", "Rishikesh", "Darjeeling", "Amritsar", "Ahmedabad"],
    "Agra": ["Udaipur", "Rishikesh", "Amritsar", "Darjeeling"],
    "Rishikesh": ["Manali", "Shimla", "Amritsar"],
    "Manali": ["Shimla", "Amritsar"],
    "Mangalore": ["Gokarna", "Coorg", "Chikmagalur", "Trivandrum", "Coimbatore"],
    "Coorg": ["Mysore", "Chikmagalur", "Mangalore", "Ooty"],
    "Mysore": ["Ooty", "Coorg", "Hampi", "Chikmagalur"],
    "Ooty": ["Coimbatore", "Mysore", "Wayanad", "Madurai"],
    "Hampi": ["Gokarna", "Mysore", "Chikmagalur"],
    "Gokarna": ["Chikmagalur", "Trivandrum"],
    "Wayanad": ["Ooty", "Coorg", "Trivandrum", "Mysore"],
    "Pondicherry": ["Madurai", "Coimbatore", "Tirupati", "Ooty"],
    "Tirupati": ["Madurai", "Pondicherry", "Coimbatore"],
    "Madurai": ["Trivandrum", "Coimbatore", "Pondicherry", "Ooty"],
    "Coimbatore": ["Trivandrum", "Ooty", "Madurai", "Mangalore"],
    "Trivandrum": ["Madurai", "Coimbatore", "Kochi", "Wayanad"],
    "Chikmagalur": ["Coorg", "Hampi", "Mangalore", "Mysore"],
    "Darjeeling": ["Amritsar", "Varanasi"],
    "Amritsar": ["Shimla", "Manali", "Udaipur"],
    "Ahmedabad": ["Udaipur", "Jaipur", "Pune", "Mumbai"],
}

# Corridors far enough apart that carriers realistically fly them.
LONG_HAUL_KM = 1200.0
MAX_FLIGHT_KM = 2400.0

# Trunk city pairs that always have non-stop service, however far apart.
NONSTOP_HUBS = {
    frozenset(p) for p in [
        ("Delhi", "Bangalore"), ("Delhi", "Mumbai"), ("Delhi", "Chennai"),
        ("Delhi", "Kolkata"), ("Delhi", "Hyderabad"), ("Mumbai", "Bangalore"),
        ("Mumbai", "Chennai"), ("Mumbai", "Kolkata"), ("Mumbai", "Hyderabad"),
        ("Bangalore", "Kolkata"), ("Bangalore", "Hyderabad"), ("Bangalore", "Chennai"),
        ("Chennai", "Kolkata"), ("Chennai", "Hyderabad"), ("Kolkata", "Hyderabad"),
        ("Delhi", "Goa"), ("Mumbai", "Goa"), ("Bangalore", "Goa"),
        ("Delhi", "Kochi"), ("Mumbai", "Kochi"), ("Bangalore", "Kochi"),
        ("Delhi", "Jaipur"), ("Mumbai", "Ahmedabad"), ("Delhi", "Ahmedabad"),
    ]
}

# Cities whose nearest commercial airport is actually in another city. Non-stop
# service exists only to/from their real airport catchment.
REGIONAL_AIR_SERVICE: Dict[str, set] = {
    "Manali": {"Delhi", "Amritsar", "Shimla"},
    "Shimla": {"Delhi", "Amritsar", "Manali"},
    "Rishikesh": {"Delhi", "Amritsar"},
    "Darjeeling": {"Kolkata", "Delhi", "Varanasi"},
    "Coorg": {"Bangalore", "Mangalore", "Mysore"},
    "Chikmagalur": {"Bangalore", "Mangalore", "Mysore"},
    "Hampi": {"Bangalore", "Hyderabad", "Goa"},
    "Gokarna": {"Bangalore", "Goa", "Mumbai"},
    "Wayanad": {"Bangalore", "Kochi", "Kozhikode"},
    "Ooty": {"Coimbatore", "Bangalore", "Chennai"},
    "Mysore": {"Bangalore", "Chennai", "Hyderabad"},
    "Pondicherry": {"Chennai", "Bangalore"},
    "Tirupati": {"Chennai", "Bangalore", "Hyderabad", "Delhi"},
    "Madurai": {"Chennai", "Bangalore", "Kochi", "Trivandrum"},
    "Coimbatore": {"Chennai", "Bangalore", "Kochi", "Delhi", "Mumbai"},
    "Mangalore": {"Bangalore", "Mumbai", "Kochi", "Goa"},
}


def airborne(origin: str, dest: str) -> bool:
    """True when a scheduled non-stop service plausibly exists for this pair."""
    if REGIONAL_AIR_SERVICE.get(origin) and dest not in REGIONAL_AIR_SERVICE[origin]:
        return False
    if REGIONAL_AIR_SERVICE.get(dest) and origin not in REGIONAL_AIR_SERVICE[dest]:
        return False
    return True
MAX_TRAIN_KM = 2600.0
MAX_BUS_KM = 750.0
MAX_FLIGHTS_PER_ROUTE = 4
MAX_TRAINS_PER_ROUTE = 4
MAX_BUSES_PER_ROUTE = 4

# Ground-transport operators per region, for plausible operator names.
TRAIN_NAMES = [
    ("Rajdhani Express", ["1A", "2A", "3A"]),
    ("Shatabdi Express", ["EC", "CC"]),
    ("Duronto Express", ["1A", "2A", "3A", "SL"]),
    ("Superfast Express", ["2A", "3A", "SL"]),
    ("Intercity Express", ["CC", "2S"]),
    ("Jan Shatabdi Express", ["CC", "2S"]),
    ("Garib Rath Express", ["3A", "CC"]),
    ("Mail Express", ["2A", "3A", "SL"]),
    ("Vande Bharat Express", ["EC", "CC"]),
    ("Humsafar Express", ["3A", "SL"]),
]

BUS_OPERATORS = [
    ("KSRTC Airavat Club Class", "Multi-Axle Volvo AC Semi-Sleeper", "https://ksrtc.in", 1.15),
    ("KSRTC FlyBus AC Sleeper", "Multi-Axle Volvo AC Sleeper", "https://ksrtc.in", 1.20),
    ("VRL Travels", "I-Shift Multi-Axle Volvo Sleeper", "https://vrlbus.in", 1.25),
    ("SRS Travels", "AC Sleeper 2+1", "https://srsbooking.com", 1.10),
    ("IntrCity SmartBus", "AC Sleeper 2+1", "https://intrcity.com", 1.18),
    ("Orange Tours & Travels", "Bharat Benz AC Sleeper", "https://orangetravels.in", 1.12),
    ("Neeta Volvo AC Seater", "Volvo 9600 AC Seater", "https://neetatravels.com", 1.05),
    ("KSRTC Karnataka Sarige", "Non-AC Seater Cum Sleeper", "https://ksrtc.in", 0.80),
    ("APSRTC Super Luxury", "AC Semi-Sleeper", "https://apsrtconline.in", 1.00),
    ("MSRTC Shivneri", "Volvo AC Seater", "https://msrtc.maharashtra.gov.in", 0.95),
    ("TSRTC Rajdhani", "AC Sleeper 2+1", "https://tsrtconline.in", 1.06),
    ("KPN Travels", "AC Sleeper 2+1", "https://kpntravels.in", 1.08),
    ("Sharma Transports", "AC Sleeper 2+1", "https://sharmatransports.com", 1.04),
    ("Rajdhani Express Travels", "AC Sleeper 2+1", "https://rajdhanitravels.in", 1.02),
]

# --------------------------------------------------------------------------- #
# Geo helpers
# --------------------------------------------------------------------------- #
def haversine_km(a: str, b: str) -> float:
    ca, cb = CITIES[a], CITIES[b]
    lat1, lon1 = math.radians(ca["lat"]), math.radians(ca["lon"])
    lat2, lon2 = math.radians(cb["lat"]), math.radians(cb["lon"])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return round(6371.0088 * 2 * math.asin(math.sqrt(h)), 1)


def road_km(a: str, b: str) -> float:
    """Indian highway factor applied to the great-circle distance."""
    return round(haversine_km(a, b) * 1.28, 1)


def clock(total_min: int) -> str:
    """'20:15' from minutes past midnight (wraps)."""
    h24, m = divmod(total_min % 1440, 60)
    return f"{h24:02d}:{m:02d}"


def clock_with_day(total_min: int, dep_min: int) -> str:
    """'08:45 (+1 day)' when the arrival crosses midnight relative to departure."""
    day_delta = total_min // 1440 - dep_min // 1440
    stamp = clock(total_min)
    if day_delta <= 0:
        return stamp
    if day_delta == 1:
        return f"{stamp} (+1 day)"
    return f"{stamp} (+{day_delta} days)"


def route_pairs() -> List[Tuple[str, str]]:
    """Every undirected corridor in the network, sorted and de-duplicated."""
    seen = set()
    pairs = []
    for origin, dests in ROUTE_NETWORK.items():
        for dest in dests:
            if dest not in CITIES:
                raise KeyError(f"route network references unknown city: {dest}")
            key = tuple(sorted((origin, dest)))
            if key in seen:
                continue
            seen.add(key)
            pairs.append((key[0], key[1]))
    return sorted(pairs)


# --------------------------------------------------------------------------- #
# Flights
# --------------------------------------------------------------------------- #
def _minutes_to_clock(start_min: int) -> Tuple[str, int]:
    """Return ('06:15 AM', day_offset) for minutes past midnight."""
    day = start_min // 1440
    mins = start_min % 1440
    h24, m = divmod(mins, 60)
    suffix = "AM" if h24 < 12 else "PM"
    h12 = h24 % 12 or 12
    return f"{h12:02d}:{m:02d} {suffix}", day


def build_flights() -> List[Dict[str, Any]]:
    rng = random.Random(20260407)
    flights: List[Dict[str, Any]] = []
    used_numbers = {f["flight_number"] for f in PRESERVED_FLIGHTS}

    def next_number(code: str) -> str:
        number = f"{code}-{rng.randint(100, 9899)}"
        while number in used_numbers:
            number = f"{code}-{rng.randint(100, 9899)}"
        used_numbers.add(number)
        return number

    def add_route(origin: str, dest: str, dist: float) -> None:
        """Both directions are scheduled: a customer asking A->B or B->A gets an answer."""
        trunk = {origin, dest} & {"Bangalore", "Delhi", "Mumbai", "Chennai", "Hyderabad", "Kolkata"}
        count = 3 if trunk else (2 if dist > 350 else 1)
        count = min(count, MAX_FLIGHTS_PER_ROUTE)
        if dist > LONG_HAUL_KM:
            count = min(count, 3)

        carriers = rng.sample(AIRLINES, count)
        # Spread departures across the operating day.
        if count == 1:
            slots = [rng.choice([390, 450, 630, 810, 990])]
        else:
            span = 870  # 06:30 -> 21:00
            step = span // count
            slots = [390 + i * step + rng.randint(-20, 20) for i in range(count)]

        for idx, (airline, code, host, factor) in enumerate(carriers):
            nonstop = dist <= LONG_HAUL_KM or frozenset((origin, dest)) in NONSTOP_HUBS
            stops = 0 if nonstop else 1
            block_h = dist / 700.0 + 0.55 + (0.9 if stops else 0.0)
            block_min = int(round(block_h * 60))
            dep_clock, dep_day = _minutes_to_clock(slots[idx])
            arr_clock, arr_day = _minutes_to_clock(slots[idx] + block_min)

            base = 1300.0 + 2.4 * dist
            price = base * factor * rng.uniform(0.95, 1.07)
            price = int(round(price / 50.0) * 50)
            price = max(1450, price)

            flights.append({
                "flight_number": next_number(code),
                "airline": airline,
                "airline_code": code,
                "origin": origin,
                "destination": dest,
                "departure_time": dep_clock,
                "arrival_time": arr_clock,
                "duration": f"{block_min // 60}h {block_min % 60:02d}m",
                "stops": stops,
                "type": "Non-stop" if stops == 0 else f"{stops} stop",
                "price": price,
                "price_inr": price,
                "currency": "INR",
                "booking_url": host,
                "distance_km": dist,
                "arrival_day_offset": arr_day - dep_day,
            })

    for city_a, city_b in route_pairs():
        dist = haversine_km(city_a, city_b)
        if dist > MAX_FLIGHT_KM:
            continue
        for origin, dest in ((city_a, city_b), (city_b, city_a)):
            if airborne(origin, dest):
                add_route(origin, dest, dist)

    flights.extend(PRESERVED_FLIGHTS)
    flights.sort(key=lambda f: (f["origin"], f["destination"], f["departure_time"]))
    return flights


# --------------------------------------------------------------------------- #
# Hotels
# --------------------------------------------------------------------------- #
# (name, rating, price/night, room type, url) templates per city tier.
HOTEL_TEMPLATES: Dict[str, List[Tuple[str, float, int, str, str]]] = {
    "metro": [
        ("The Leela Palace {city}", 4.8, 14500, "Royal Premier Room", "https://theleela.com"),
        ("ITC {city}, a Luxury Collection Hotel", 4.7, 10200, "Executive Club Suite", "https://itchotels.com"),
        ("Taj {city}", 4.8, 13000, "Deluxe City View Room", "https://tajhotels.com"),
        ("Radisson Blu {city} City Centre", 4.3, 6200, "Superior King Room", "https://radissonhotels.com"),
        ("Novotel {city} {region}", 4.4, 5800, "Executive King Room", "https://accor.com"),
        ("Ibis {city} City Centre", 4.1, 3800, "Standard Queen Room", "https://accor.com"),
        ("Treebo Trend {city} Stay", 3.9, 2100, "Deluxe Double Room", "https://treebo.com"),
        ("Zostel {city}", 4.2, 1200, "Private Deluxe Room", "https://zostel.com"),
    ],
    "leisure": [
        ("Taj Exotica Resort & Spa, {city}", 4.8, 12500, "Luxury Sea View Suite", "https://tajhotels.com"),
        ("WelcomHeritage {city} Resort", 4.5, 7400, "Heritage Garden Room", "https://welcomheritagehotels.in"),
        ("Novotel {city} Resort & Spa", 4.4, 5800, "Executive King Room", "https://accor.com"),
        ("Sterling {city}", 4.3, 4600, "Premier Valley View Room", "https://sterlingholidays.com"),
        ("The Fern Residency {city}", 4.1, 3200, "Deluxe Twin Room", "https://fernhotels.com"),
        ("Zostel {city}", 4.2, 1500, "Private Deluxe Room", "https://zostel.com"),
        ("OYO Townhouse {city}", 3.8, 1400, "Standard Double Room", "https://oyorooms.com"),
    ],
    "heritage": [
        ("Rambagh Palace, {city}", 4.9, 28000, "Royal Suite", "https://tajhotels.com"),
        ("Trident, {city}", 4.6, 8800, "Premier Room", "https://tridenthotels.com"),
        ("WelcomHotel {city}", 4.5, 6500, "Deluxe Room", "https://itchotels.com"),
        ("Alsisar Haveli {city}", 4.4, 5200, "Heritage Suite", "https://alsisarhaveli.com"),
        ("Hotel Pearl Palace {city}", 4.3, 2400, "Deluxe Double Room", "https://hotelpearlpalace.com"),
        ("Zostel {city}", 4.2, 1200, "Private Deluxe Room", "https://zostel.com"),
    ],
    "temple": [
        ("Marasa Sarovar Premiere {city}", 4.5, 7200, "Executive Suite", "https://sarovarhotels.com"),
        ("Fortune Select {city}", 4.2, 4400, "Club Room", "https://fortunehotels.in"),
        ("The Gateway Hotel {city}", 4.3, 5200, "Superior Room", "https://tajhotels.com"),
        ("Hotel Annapoorna {city}", 4.0, 2200, "Deluxe AC Room", "https://annapoornahotels.com"),
        ("Zostel {city}", 4.1, 1100, "Private Deluxe Room", "https://zostel.com"),
    ],
}

LEISURE_CITIES = {"Goa", "Manali", "Shimla", "Ooty", "Coorg", "Hampi", "Gokarna", "Wayanad",
                  "Chikmagalur", "Pondicherry", "Mysore", "Mangalore", "Rishikesh", "Darjeeling"}
HERITAGE_CITIES = {"Jaipur", "Udaipur", "Agra", "Varanasi", "Amritsar"}
TEMPLE_CITIES = {"Tirupati", "Madurai", "Coimbatore", "Trivandrum", "Kochi"}

# Hotels already shipped by hand; preserved to avoid breaking UI expectations.
PRESERVED_HOTELS: Dict[str, List[Dict[str, Any]]] = {
    "goa": [
        {"hotel_name": "Taj Exotica Resort & Spa, Goa", "rating": 4.8, "price_per_night": 12500,
         "room_type": "Luxury Sea View Suite", "city": "Goa", "hotel_url": "https://www.tajhotels.com"},
        {"hotel_name": "Novotel Goa Resort & Spa", "rating": 4.4, "price_per_night": 5800,
         "room_type": "Executive King Room", "city": "Goa", "hotel_url": "https://accor.com"},
        {"hotel_name": "Zostel Goa (Anjuna)", "rating": 4.2, "price_per_night": 1800,
         "room_type": "Private Deluxe Room", "city": "Goa", "hotel_url": "https://zostel.com"},
    ],
    "bangalore": [
        {"hotel_name": "The Leela Palace Bengaluru", "rating": 4.9, "price_per_night": 14500,
         "room_type": "Royal Premier Room", "city": "Bangalore", "hotel_url": "https://theleela.com"},
        {"hotel_name": "ITC Gardenia, a Luxury Collection Hotel", "rating": 4.7, "price_per_night": 9500,
         "room_type": "Executive Club Suite", "city": "Bangalore", "hotel_url": "https://marriott.com"},
        {"hotel_name": "Ibis Bengaluru City Centre", "rating": 4.1, "price_per_night": 3800,
         "room_type": "Standard Queen Room", "city": "Bangalore", "hotel_url": "https://accor.com"},
    ],
    "delhi": [
        {"hotel_name": "The Taj Mahal Hotel, New Delhi", "rating": 4.8, "price_per_night": 13000,
         "room_type": "Deluxe City View Room", "city": "Delhi", "hotel_url": "https://tajhotels.com"},
        {"hotel_name": "Radisson Blu Marina Connaught Place", "rating": 4.3, "price_per_night": 6200,
         "room_type": "Superior King Room", "city": "Delhi", "hotel_url": "https://radissonhotels.com"},
    ],
    "mumbai": [
        {"hotel_name": "The Taj Mahal Palace, Mumbai", "rating": 4.9, "price_per_night": 18000,
         "room_type": "Heritage Sea View Room", "city": "Mumbai", "hotel_url": "https://tajhotels.com"},
        {"hotel_name": "Trident Hotel, Nariman Point", "rating": 4.6, "price_per_night": 8800,
         "room_type": "Premier Ocean View", "city": "Mumbai", "hotel_url": "https://tridenthotels.com"},
    ],
    "mysore": [
        {"hotel_name": "Grand Mercure Mysore", "rating": 4.5, "price_per_night": 4500,
         "room_type": "Deluxe King Room", "city": "Mysore", "hotel_url": "https://accor.com"},
    ],
}


def _tier_for(city: str) -> str:
    if city in HERITAGE_CITIES:
        return "heritage"
    if city in LEISURE_CITIES:
        return "leisure"
    if city in TEMPLE_CITIES:
        return "temple"
    return "metro"


def build_hotels() -> Dict[str, List[Dict[str, Any]]]:
    rng = random.Random(7788)
    hotels: Dict[str, List[Dict[str, Any]]] = {}

    for city in sorted(CITIES):
        tier = _tier_for(city)
        region = CITIES[city]["region"]
        rows = []
        for name, rating, price, room, url in HOTEL_TEMPLATES[tier]:
            jitter = rng.uniform(0.94, 1.06)
            rows.append({
                "hotel_name": name.format(city=city, region=region),
                "rating": round(min(4.9, rating + rng.uniform(-0.15, 0.1)), 1),
                "price_per_night": int(round(price * jitter / 100.0) * 100),
                "room_type": room,
                "city": city,
                "hotel_url": url,
            })
        rows.sort(key=lambda r: -r["rating"])
        hotels[city.lower()] = rows

    # Preserved hand-written rows win.
    for key, rows in PRESERVED_HOTELS.items():
        hotels[key] = rows

    # Common aliases the intent layer emits.
    for alias, canonical in (("bengaluru", "bangalore"), ("new delhi", "delhi"),
                             ("mysuru", "mysore"), ("pondy", "pondicherry"),
                             ("cochin", "kochi"), ("ernakulam", "kochi"),
                             ("benares", "varanasi"), ("kashi", "varanasi")):
        if canonical in hotels:
            hotels[alias] = hotels[canonical]

    return dict(sorted(hotels.items()))


# --------------------------------------------------------------------------- #
# Trains
# --------------------------------------------------------------------------- #
# (name, classes, rupees per km)
TRAIN_CLASSES: Dict[str, Tuple[List[str], float]] = {
    "Vande Bharat Express": (["EC", "CC"], 1.85),
    "Rajdhani Express": (["1A", "2A", "3A"], 1.70),
    "Shatabdi Express": (["EC", "CC"], 1.45),
    "Duronto Express": (["1A", "2A", "3A", "SL"], 1.25),
    "Humsafar Express": (["3A", "SL"], 0.95),
    "Garib Rath Express": (["3A", "CC"], 0.80),
    "Superfast Express": (["2A", "3A", "SL"], 0.90),
    "Mail Express": (["2A", "3A", "SL"], 0.72),
    "Intercity Express": (["CC", "2S"], 0.62),
    "Jan Shatabdi Express": (["CC", "2S"], 0.58),
}


def build_trains() -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Dict[str, Any]]]:
    rng = random.Random(4242)
    trains: Dict[str, List[Dict[str, Any]]] = {}
    statuses: Dict[str, Dict[str, Any]] = {}

    used_numbers = set()

    for origin, dest in route_pairs():
        dist = road_km(origin, dest)
        if dist > MAX_TRAIN_KM:
            continue
        trunk = {origin, dest} & {"Bangalore", "Delhi", "Mumbai", "Chennai", "Hyderabad", "Kolkata", "Pune"}
        count = 3 if trunk else (2 if dist > 250 else 1)
        count = min(count, MAX_TRAINS_PER_ROUTE)

        # Realistic average speeds including slack for stops.
        speed = 58.0 if dist > 700 else (50.0 if dist > 250 else 42.0)
        travel_min = int(round(dist / speed * 60)) + 25

        rows = []
        names = rng.sample(list(TRAIN_CLASSES), count)
        for idx, name in enumerate(names):
            classes, per_km = TRAIN_CLASSES[name]
            number = str(rng.randint(11000, 22999))
            while number in used_numbers:
                number = str(rng.randint(11000, 22999))
            used_numbers.add(number)

            # Departures spread from early morning to late evening.
            base_slots = [7 * 60 + 15, 13 * 60 + 40, 16 * 60 + 50, 20 * 60 + 10]
            dep_min = base_slots[idx % len(base_slots)] + rng.randint(-25, 25)
            arr_min = dep_min + travel_min

            # Sleeper-class fare of the cheapest class on the train; AC travel costs more.
            fare = int(round((240 + per_km * dist) / 10.0) * 10)

            rows.append({
                "train_number": number,
                "train_name": f"{origin} - {dest} {name}",
                "origin": origin,
                "destination": dest,
                "departure": clock_with_day(dep_min, dep_min),
                "arrival": clock_with_day(arr_min, dep_min),
                "duration": f"{travel_min // 60}h {travel_min % 60:02d}m",
                "fare": fare,
                "classes": classes,
                "distance_km": dist,
                "provider_url": "https://www.irctc.co.in",
            })

        rows.sort(key=lambda r: r["departure"])
        trains[f"{origin.lower()}-{dest.lower()}"] = rows

        # India's rail network runs both ways on the same corridor: same stock,
        # mirrored schedule (departure recomputed from the duration).
        reverse = []
        for row in rows:
            rev = dict(row)
            rev["origin"], rev["destination"] = dest, origin
            rev["train_name"] = row["train_name"].replace(f"{origin} - {dest}", f"{dest} - {origin}")
            dep_min = int(row["departure"][:2]) * 60 + int(row["departure"][3:5])
            rev["departure"] = clock_with_day(dep_min, dep_min)
            rev["arrival"] = clock_with_day(dep_min + travel_min, dep_min)
            reverse.append(rev)
        trains[f"{dest.lower()}-{origin.lower()}"] = reverse

        # Running status for the lead train of the outward leg.
        lead = rows[0]
        delay = rng.choice([0, 0, 0, 0, 5, 12, 25, 40])
        statuses[lead["train_number"]] = {
            "train_number": lead["train_number"],
            "train_name": lead["train_name"],
            "status": "Running On Time" if delay == 0 else f"Running Late by {delay} mins",
            "current_station": f"{dest} Division Control Room",
            "last_passed_station": origin,
            "next_station": dest,
            "delay_minutes": delay,
        }

    return dict(sorted(trains.items())), dict(sorted(statuses.items()))


# --------------------------------------------------------------------------- #
# Buses
# --------------------------------------------------------------------------- #
def build_buses() -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Dict[str, Any]]]:
    rng = random.Random(9911)
    buses: Dict[str, List[Dict[str, Any]]] = {}
    statuses: Dict[str, Dict[str, Any]] = {}

    for origin, dest in route_pairs():
        dist = road_km(origin, dest)
        if dist > MAX_BUS_KM:
            continue
        count = 3 if dist > 200 else 2
        count = min(count, MAX_BUSES_PER_ROUTE)
        if dist > 500:
            count = min(count, 2)

        rows = []
        operators = rng.sample(BUS_OPERATORS, count)
        for idx, (operator, bus_type, url, factor) in enumerate(operators):
            overnight = dist > 320
            if overnight:
                dep_min = 20 * 60 + idx * 45 + rng.randint(-25, 25)
            else:
                dep_min = 6 * 60 + idx * 105 + rng.randint(-20, 20)
            dep_min = max(5 * 60, min(dep_min, 23 * 60 + 55))

            travel_min = int(round(dist / (48.0 if overnight else 42.0) * 60)) + 20
            arr_min = dep_min + travel_min

            fare = int(round((200 + dist * 1.30 * factor) / 10.0) * 10)

            rows.append({
                "operator": operator,
                "bus_type": bus_type,
                "origin": origin,
                "destination": dest,
                "departure": clock_with_day(dep_min, dep_min),
                "arrival": clock_with_day(arr_min, dep_min),
                "duration": f"{travel_min // 60}h {travel_min % 60:02d}m",
                "fare": fare,
                "distance_km": dist,
                "booking_url": url,
            })

        rows.sort(key=lambda r: r["departure"])
        buses[f"{origin.lower()}-{dest.lower()}"] = rows

        reverse = []
        for row in rows:
            rev = dict(row)
            rev["origin"], rev["destination"] = dest, origin
            dep_min = int(row["departure"][:2]) * 60 + int(row["departure"][3:5])
            rev["departure"] = clock_with_day(dep_min, dep_min)
            rev["arrival"] = clock_with_day(dep_min + travel_min, dep_min)
            reverse.append(rev)
        buses[f"{dest.lower()}-{origin.lower()}"] = reverse

        # Live-status rows are keyed by operator name and route, so a lookup by
        # operator, route or service name all resolve to something real.
        for row in rows:
            delay = rng.choice([0, 0, 0, 0, 10, 20, 35])
            statuses[f"{row['operator']} | {origin}-{dest}"] = {
                "bus_identifier": row["operator"],
                "operator": row["operator"],
                "route": f"{origin} - {dest}",
                "bus_type": row["bus_type"],
                "current_location": f"{origin} - {dest} Highway Corridor",
                "status": "Running On Time" if delay == 0 else f"Running Late by {delay} mins",
                "delay_minutes": delay,
                "eta": row["arrival"],
            }

    return dict(sorted(buses.items())), dict(sorted(statuses.items()))


# --------------------------------------------------------------------------- #
# Weather
# --------------------------------------------------------------------------- #
# (condition, temp low, temp high, humidity, precipitation, clothing)
CLIMATE_PROFILES = {
    "coastal-south": ("Tropical Sunny / Warm Coastal Breeze", 24, 32, 68, 20,
                      "Light linen clothing, sunscreen, and beachwear recommended."),
    "coastal-west": ("Coastal Warm & Humid", 25, 33, 75, 20,
                     "Cotton wear and stay well hydrated."),
    "plateau": ("Mild & Pleasant", 19, 29, 55, 15,
                "Comfortable light jacket for early morning or late evening."),
    "deccan": ("Warm & Partially Cloudy", 22, 33, 50, 10,
               "Comfortable summer attire."),
    "ganga-plains": ("Clear Sky / Warm", 22, 34, 45, 5,
                     "Breathable cotton clothes and sunglasses."),
    "arid": ("Sunny & Dry", 23, 36, 35, 0,
             "Light cotton clothing, hat, and sunscreen."),
    "himalayan": ("Cool & Crisp Mountain Air", 6, 18, 60, 25,
                  "Warm layers, a windproof jacket, and sturdy walking shoes."),
    "hill-south": ("Pleasant & Clear Hill Climate", 14, 24, 70, 30,
                   "Light woollens for the evening and comfortable walking shoes."),
    "bengal-coastal": ("Humid & Partly Cloudy Coastal", 24, 32, 78, 25,
                       "Light breathable fabrics and an umbrella."),
}

CITY_CLIMATE = {
    "Goa": "coastal-west", "Mumbai": "coastal-west", "Mangalore": "coastal-west",
    "Gokarna": "coastal-west", "Kochi": "bengal-coastal", "Trivandrum": "bengal-coastal",
    "Chennai": "bengal-coastal", "Pondicherry": "bengal-coastal",
    "Bangalore": "plateau", "Mysore": "plateau", "Coorg": "hill-south",
    "Chikmagalur": "hill-south", "Ooty": "hill-south", "Wayanad": "hill-south",
    "Hyderabad": "deccan", "Pune": "deccan", "Hampi": "deccan",
    "Delhi": "ganga-plains", "Agra": "ganga-plains", "Varanasi": "ganga-plains",
    "Kolkata": "ganga-plains", "Amritsar": "ganga-plains",
    "Jaipur": "arid", "Udaipur": "arid", "Ahmedabad": "arid",
    "Manali": "himalayan", "Shimla": "himalayan", "Rishikesh": "himalayan",
    "Darjeeling": "himalayan",
    "Tirupati": "deccan", "Madurai": "deccan", "Coimbatore": "plateau",
}

CITY_ALIASES = {
    "bengaluru": "Bangalore", "new delhi": "Delhi", "mysuru": "Mysore",
    "pondy": "Pondicherry", "cochin": "Kochi", "ernakulam": "Kochi",
    "benares": "Varanasi", "kashi": "Varanasi", "bombay": "Mumbai",
    "madras": "Chennai", "calcutta": "Kolkata", "gurgaon": "Delhi",
    "noida": "Delhi", "chikmagalur": "Chikmagalur",
}


def build_weather() -> Dict[str, Dict[str, Any]]:
    weather: Dict[str, Dict[str, Any]] = {}
    for city in sorted(CITIES):
        condition, low, high, humidity, precip, clothing = CLIMATE_PROFILES[CITY_CLIMATE[city]]
        weather[city.lower()] = {
            "city": city,
            "condition": condition,
            "temperature": round((low + high) / 2.0, 1),
            "temperature_range": f"{low}°C - {high}°C",
            "humidity": f"{humidity}%",
            "precipitation_chance": f"{precip}%",
            "clothing_recommendation": clothing,
        }
    for alias, canonical in CITY_ALIASES.items():
        if canonical.lower() in weather:
            weather[alias] = {**weather[canonical.lower()], "city": canonical}
    return dict(sorted(weather.items()))


# --------------------------------------------------------------------------- #
# Write
# --------------------------------------------------------------------------- #
def write_json(name: str, payload: Any) -> int:
    path = DATA_DIR / name
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")
    return len(text)


def main() -> None:
    flights = build_flights()
    hotels = build_hotels()
    trains, train_status = build_trains()
    buses, bus_status = build_buses()
    weather = build_weather()

    sizes = {
        "flights.json": write_json("flights.json", flights),
        "hotels.json": write_json("hotels.json", hotels),
        "trains.json": write_json("trains.json", {"trains": trains, "statuses": train_status}),
        "buses.json": write_json("buses.json", {"buses": buses, "statuses": bus_status}),
        "weather.json": write_json("weather.json", weather),
    }

    flight_routes = {(f["origin"], f["destination"]) for f in flights}
    print(f"flights.json  : {len(flights):5d} flights on {len(flight_routes):4d} directed routes")
    print(f"hotels.json   : {sum(len(v) for v in hotels.values()):5d} hotels in {len(hotels):3d} city keys")
    print(f"trains.json   : {sum(len(v) for v in trains.values()):5d} trains on {len(trains):4d} directed routes, "
          f"{len(train_status)} running statuses")
    print(f"buses.json    : {sum(len(v) for v in buses.values()):5d} buses on {len(buses):4d} directed routes, "
          f"{len(bus_status)} running statuses")
    print(f"weather.json  : {len(weather):5d} city keys")
    print("bytes         : " + ", ".join(f"{k}={v}" for k, v in sizes.items()))

    cities = sorted(CITIES)
    print(f"cities ({len(cities)}): " + ", ".join(cities))


if __name__ == "__main__":
    main()
