"""
Standardized JSON Normalization Layer.

Ensures every JSON mode response returns a consistent internal schema across:
flights, hotels, trains, buses, weather, routes, cabs, trip planning, shipment tracking, drivers, vehicles.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


def build_json_response(
    intent: str,
    status: str,
    data: Optional[Any],
    source: str = "provider",
    data_mode: str = "live",
    is_mock: bool = False,
    error_code: Optional[str] = None,
    message: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """
    Consistent internal JSON response schema:

    {
      "mode": "JSON",
      "intent": "flight_search",
      "status": "success",
      "data": {},
      "source": "provider_or_database",
      "data_mode": "live|database|demo|unavailable",
      "is_mock": false,
      "fetched_at": "ISO-8601 timestamp"
    }
    """
    fetched_at = datetime.now(timezone.utc).isoformat()
    res: Dict[str, Any] = {
        "mode": "JSON",
        "intent": intent,
        "status": status,
        "data": data,
        "source": source,
        "data_mode": data_mode,
        "is_mock": is_mock,
        "fetched_at": fetched_at,
    }
    if error_code:
        res["error_code"] = error_code
    if message:
        res["message"] = message
    res.update(extra)
    return res


def normalize_flight(item: Dict[str, Any], origin: Optional[str] = None, destination: Optional[str] = None, date: Optional[str] = None) -> Dict[str, Any]:
    return {
        "flight_number": item.get("flight_number") or item.get("flight") or item.get("number") or "N/A",
        "airline": item.get("airline") or item.get("operator") or item.get("carrier") or "N/A",
        "origin": item.get("origin") or item.get("departure_airport") or origin or "N/A",
        "destination": item.get("destination") or item.get("arrival_airport") or destination or "N/A",
        "date": item.get("flight_date") or item.get("date") or date,
        "return_date": item.get("return_date"),
        "passengers": item.get("passengers", 1),
        "cabin_class": item.get("cabin_class") or item.get("class") or "Economy",
        "departure_time": item.get("departure_time") or item.get("scheduled_departure") or item.get("departure") or "N/A",
        "arrival_time": item.get("arrival_time") or item.get("scheduled_arrival") or item.get("arrival") or "N/A",
        "duration": item.get("duration") or "N/A",
        "stops": item.get("stops", 0),
        "price": item.get("price") or item.get("price_inr") or item.get("cost") or 0,
        "currency": item.get("currency", "INR"),
        "baggage": item.get("baggage") or item.get("baggage_allowance") or "15 kg",
        "status": item.get("status") or item.get("flight_status") or "scheduled",
        "booking_url": item.get("booking_url") or item.get("url") or item.get("provider_url"),
    }


def normalize_hotel(item: Dict[str, Any], city: Optional[str] = None) -> Dict[str, Any]:
    return {
        "hotel_name": item.get("hotel_name") or item.get("name") or "N/A",
        "city": item.get("city") or item.get("location") or city or "N/A",
        "check_in": item.get("check_in"),
        "check_out": item.get("check_out"),
        "adults": item.get("adults", 1),
        "children": item.get("children", 0),
        "rooms": item.get("rooms", 1),
        "rating": item.get("rating") or item.get("stars") or 4.0,
        "review_count": item.get("review_count") or item.get("reviews") or 0,
        "address": item.get("address") or item.get("location") or "N/A",
        "amenities": item.get("amenities") or ["WiFi", "Air Conditioning", "Breakfast"],
        "room_type": item.get("room_type") or "Deluxe Room",
        "price_per_night": item.get("price_per_night") or item.get("price") or 0,
        "total_price": item.get("total_price") or item.get("price") or 0,
        "currency": item.get("currency", "INR"),
        "availability": item.get("availability", True),
        "provider": item.get("provider") or item.get("source") or "hotel_provider",
        "hotel_url": item.get("hotel_url") or item.get("booking_url"),
    }


def normalize_train(item: Dict[str, Any], origin: Optional[str] = None, destination: Optional[str] = None) -> Dict[str, Any]:
    return {
        "train_number": item.get("train_number") or item.get("number") or "N/A",
        "train_name": item.get("train_name") or item.get("name") or "Express",
        "origin": item.get("origin") or item.get("departure_station") or origin or "N/A",
        "destination": item.get("destination") or item.get("arrival_station") or destination or "N/A",
        "date": item.get("date") or item.get("travel_date"),
        "passengers": item.get("passengers", 1),
        "departure": item.get("departure") or item.get("departure_time") or "N/A",
        "arrival": item.get("arrival") or item.get("arrival_time") or "N/A",
        "duration": item.get("duration") or "N/A",
        "available_classes": item.get("available_classes") or ["1A", "2A", "3A", "SL"],
        "seat_availability": item.get("seat_availability") or item.get("status") or "Available",
        "fare": item.get("fare") or item.get("price") or 0,
        "currency": item.get("currency", "INR"),
        "provider_url": item.get("provider_url") or item.get("booking_url"),
    }


def normalize_bus(item: Dict[str, Any], origin: Optional[str] = None, destination: Optional[str] = None) -> Dict[str, Any]:
    return {
        "operator": item.get("operator") or item.get("name") or "Express Bus",
        "bus_type": item.get("bus_type") or item.get("type") or "AC Sleeper",
        "origin": item.get("origin") or origin or "N/A",
        "destination": item.get("destination") or destination or "N/A",
        "date": item.get("date") or item.get("travel_date"),
        "passengers": item.get("passengers", 1),
        "departure": item.get("departure") or item.get("departure_time") or "N/A",
        "arrival": item.get("arrival") or item.get("arrival_time") or "N/A",
        "duration": item.get("duration") or "N/A",
        "seats_available": item.get("seats_available") or item.get("seats") or 10,
        "fare": item.get("fare") or item.get("price") or 0,
        "currency": item.get("currency", "INR"),
        "booking_url": item.get("booking_url"),
    }


def normalize_weather(item: Dict[str, Any], city: Optional[str] = None) -> Dict[str, Any]:
    return {
        "city": item.get("city") or item.get("location") or city or "N/A",
        "latitude": item.get("latitude") or item.get("lat"),
        "longitude": item.get("longitude") or item.get("lon"),
        "temperature": item.get("temperature") or item.get("temp") or item.get("temp_c") or 25.0,
        # Static climate references describe a range, not a single reading.
        "temperature_range": item.get("temperature_range") or item.get("temp_range"),
        "precipitation_chance": item.get("precipitation_chance") or item.get("precipitation"),
        "feels_like": item.get("feels_like") or item.get("feels_like_c") or 25.0,
        "humidity": item.get("humidity") or 60,
        "wind_speed": item.get("wind_speed") or item.get("wind_kph") or 10.0,
        "condition": item.get("condition") or item.get("description") or "Clear",
        "visibility": item.get("visibility") or 10.0,
        "rainfall": item.get("rainfall") or item.get("precipitation") or 0.0,
        "clothing_recommendation": item.get("clothing_recommendation"),
        "forecast": item.get("forecast") or [],
        "observation_time": item.get("observation_time") or datetime.now(timezone.utc).isoformat(),
        "source": item.get("source") or "weather_provider",
        "fetched_at": item.get("fetched_at") or datetime.now(timezone.utc).isoformat(),
    }


def normalize_route(item: Dict[str, Any], origin: Optional[str] = None, destination: Optional[str] = None) -> Dict[str, Any]:
    distance_val = item.get("distance") or item.get("road_distance_estimate_km") or item.get("distance_km")
    if isinstance(distance_val, (int, float)):
        distance_str = f"{distance_val} km"
    else:
        distance_str = str(distance_val or "N/A")

    duration_val = item.get("duration") or item.get("duration_formatted") or item.get("travel_time") or item.get("duration_minutes")
    if isinstance(duration_val, (int, float)):
        hours, mins = divmod(int(duration_val), 60)
        duration_str = f"{hours}h {mins}m" if hours else f"{mins} mins"
    else:
        duration_str = str(duration_val or "N/A")

    return {
        "origin": item.get("origin") or origin or "N/A",
        "destination": item.get("destination") or destination or "N/A",
        "distance": distance_str,
        "duration": duration_str,
        "traffic_duration": item.get("traffic_duration") or duration_str,
        "route": item.get("recommended_route") or item.get("route") or item.get("summary") or "Primary Route",
        "waypoints": item.get("waypoints") or [],
        "transport_mode": item.get("travel_mode") or item.get("transport_mode") or "driving",
        "tolls": item.get("tolls") or "Applicable",
        "fuel_estimate": item.get("fuel_estimate") or "N/A",
        "maps_url": item.get("maps_url") or item.get("google_maps_url"),
    }


def normalize_cab(item: Dict[str, Any], pickup: Optional[str] = None, drop: Optional[str] = None) -> Dict[str, Any]:
    return {
        "pickup": item.get("pickup") or item.get("origin") or pickup or "N/A",
        "drop": item.get("drop") or item.get("destination") or drop or "N/A",
        "vehicle_type": item.get("vehicle_type") or item.get("type") or "Sedan",
        "provider": item.get("provider") or "TravelLogix Cabs",
        "estimated_fare": item.get("estimated_fare") or item.get("fare") or 500,
        "currency": item.get("currency", "INR"),
        "estimated_time": item.get("estimated_time") or item.get("eta") or "15 mins",
        "availability": item.get("availability", True),
        "booking_url": item.get("booking_url"),
    }


def normalize_shipment(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tracking_id": item.get("tracking_id") or "N/A",
        "shipment_id": item.get("shipment_id") or item.get("id") or item.get("tracking_id"),
        "status": item.get("status") or "Registered",
        "origin": item.get("origin") or "N/A",
        "destination": item.get("destination") or "N/A",
        "current_location": item.get("current_location") or item.get("verified_location") or "N/A",
        "driver": item.get("driver"),
        "vehicle": item.get("vehicle"),
        "estimated_delivery": item.get("expected_delivery_date") or item.get("estimated_delivery"),
        "last_updated": item.get("last_updated"),
        "location_history": item.get("location_history") or item.get("events") or [],
        "status_history": item.get("status_history") or item.get("events") or [],
        "source": item.get("source") or "travelogix_database",
        "data_mode": item.get("data_mode") or item.get("mode") or "live",
        "is_demo": bool(item.get("is_demo") or item.get("is_mock")),
    }


def normalize_driver(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "driver_id": item.get("driver_id") or item.get("id") or "N/A",
        "name": item.get("name") or item.get("full_name") or "N/A",
        "phone": item.get("phone"),
        "status": item.get("status") or "Active",
        "assigned_vehicle": item.get("assigned_vehicle") or item.get("vehicle"),
        "assigned_shipment": item.get("assigned_shipment") or item.get("shipment"),
        "current_location": item.get("current_location"),
    }


def normalize_vehicle(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "vehicle_id": item.get("vehicle_id") or item.get("id") or "N/A",
        "vehicle_number": item.get("vehicle_number") or item.get("registration_number") or "N/A",
        "type": item.get("type") or item.get("model") or "Truck",
        "status": item.get("status") or "Active",
        "driver": item.get("driver"),
        "assigned_shipment": item.get("assigned_shipment"),
        "current_location": item.get("current_location"),
    }
