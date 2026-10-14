import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import logger
from app.models.driver import Driver
from app.models.driver_location import DriverLocation
from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.vehicle import Vehicle
from app.services.audit_service import create_audit_log
from app.services.driver_service import get_driver_by_id
from app.services.shipment_service import get_shipment_by_id_or_tracking, update_shipment_status
from app.services.vehicle_service import get_vehicle_by_id

# Operational statuses that count as "the driver is currently on a run".
ACTIVE_RUN_STATUSES = ("PICKUP_SCHEDULED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELAYED")

EVENTS_PER_SHIPMENT_LIMIT = 200
LOCATIONS_PER_DRIVER_LIMIT = 20


async def get_shipment_events(
    db: AsyncSession,
    tracking_id_or_shipment_id: str,
    limit: int = EVENTS_PER_SHIPMENT_LIMIT,
) -> List[ShipmentEvent]:
    shipment = await get_shipment_by_id_or_tracking(db, tracking_id_or_shipment_id)
    if not shipment:
        return []
    return await get_shipment_events_for_shipment(db, shipment, limit=limit)


async def get_shipment_events_for_shipment(
    db: AsyncSession,
    shipment: Shipment,
    limit: int = EVENTS_PER_SHIPMENT_LIMIT,
) -> List[ShipmentEvent]:
    """Event list for an already-loaded shipment (avoids a redundant re-fetch)."""
    stmt = (
        select(ShipmentEvent)
        .where(ShipmentEvent.shipment_id == shipment.id)
        .order_by(ShipmentEvent.timestamp.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


CITY_COORDINATES = {
    "mumbai": {"lat": 19.0760, "lng": 72.8777},
    "mumbai hub": {"lat": 19.0760, "lng": 72.8777},
    "mumbai dispatch hub": {"lat": 19.0760, "lng": 72.8777},
    "delhi": {"lat": 28.6139, "lng": 77.2090},
    "delhi ncr": {"lat": 28.6139, "lng": 77.2090},
    "delhi central freight yard": {"lat": 28.6139, "lng": 77.2090},
    "bangalore": {"lat": 12.9716, "lng": 77.5946},
    "bangalore hub": {"lat": 12.9716, "lng": 77.5946},
    "bangalore hub depot": {"lat": 12.9716, "lng": 77.5946},
    "goa": {"lat": 15.2993, "lng": 74.1240},
    "pune": {"lat": 18.5204, "lng": 73.8567},
    "pune highway express control": {"lat": 18.5204, "lng": 73.8567},
    "mysore": {"lat": 12.2958, "lng": 76.6394},
    "mysore road highway transit hub": {"lat": 12.2958, "lng": 76.6394},
    "kolhapur": {"lat": 16.7050, "lng": 74.2433},
    "kolhapur toll hub": {"lat": 16.7050, "lng": 74.2433},
}


def resolve_coordinates(location_str: Optional[str]) -> Optional[Dict[str, float]]:
    if not location_str:
        return None
    loc_lower = location_str.strip().lower()
    for key, coords in CITY_COORDINATES.items():
        if key in loc_lower or loc_lower in key:
            return coords
    return None


def _source_name() -> str:
    """Report the dialect actually in use instead of claiming PostgreSQL."""
    try:
        from app.db.session import engine

        return f"travelogix_{engine.dialect.name}_db"
    except Exception:  # pragma: no cover
        return "travelogix_db"


async def get_shipment_tracking_full(db: AsyncSession, tracking_id_or_id: str) -> Dict[str, Any]:
    shipment = await get_shipment_by_id_or_tracking(db, tracking_id_or_id)
    if not shipment:
        raise AppException(
            message=f"Tracking ID '{tracking_id_or_id}' not found.",
            code="TRACKING_NOT_FOUND",
            status_code=404,
        )

    # Pass the loaded shipment so the row is not fetched twice.
    events = await get_shipment_events_for_shipment(db, shipment)

    driver = None
    if shipment.assigned_driver_id:
        driver = await get_driver_by_id(db, shipment.assigned_driver_id)

    vehicle = None
    if shipment.assigned_vehicle_id:
        vehicle = await get_vehicle_by_id(db, shipment.assigned_vehicle_id)

    curr_loc = shipment.current_location or shipment.origin
    orig_coords = resolve_coordinates(shipment.origin)
    dest_coords = resolve_coordinates(shipment.destination)
    curr_coords = resolve_coordinates(curr_loc)

    route_points = []
    if orig_coords:
        route_points.append([orig_coords["lat"], orig_coords["lng"]])
    if curr_coords and (not orig_coords or curr_coords != orig_coords):
        route_points.append([curr_coords["lat"], curr_coords["lng"]])
    if dest_coords and (not curr_coords or dest_coords != curr_coords):
        route_points.append([dest_coords["lat"], dest_coords["lng"]])

    return {
        "shipment": shipment,
        "tracking_id": shipment.tracking_id,
        "status": shipment.status,
        "current_location": curr_loc,
        "current_coordinates": curr_coords,
        "origin": shipment.origin,
        "origin_coordinates": orig_coords,
        "destination": shipment.destination,
        "destination_coordinates": dest_coords,
        "route_points": route_points if len(route_points) >= 2 else [],
        "customer_name": shipment.customer_name,
        "customer_email": shipment.customer_email,
        "expected_delivery_date": shipment.expected_delivery_date,
        "actual_delivery_date": shipment.actual_delivery_date,
        "driver": driver,
        "vehicle": vehicle,
        "events": events,
        "source": _source_name(),
        "mode": "demo" if shipment.is_demo else "live",
        "is_mock": bool(shipment.is_demo),
        "last_updated": shipment.updated_at.isoformat() if shipment.updated_at else datetime.now(timezone.utc).isoformat(),
    }


def _location_history(locations: List[DriverLocation]) -> List[Dict[str, Any]]:
    return [
        {
            "id": loc.id,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "accuracy": loc.accuracy,
            "location_name": loc.location_name,
            "recorded_at": loc.recorded_at.isoformat() if loc.recorded_at else None,
        }
        for loc in locations
    ]


def _driver_tracking_payload(
    driver: Driver,
    vehicle: Optional[Vehicle],
    active_shipment: Optional[Shipment],
    locations: List[DriverLocation],
) -> Dict[str, Any]:
    latest_loc = locations[0] if locations else None
    return {
        "driver": driver,
        "driver_id": driver.driver_id,
        "full_name": driver.full_name,
        "phone": driver.phone,
        "status": driver.status,
        "current_location": latest_loc.location_name
        if latest_loc
        else (driver.current_location or "Depot Location"),
        "latitude": latest_loc.latitude if latest_loc else None,
        "longitude": latest_loc.longitude if latest_loc else None,
        "accuracy": latest_loc.accuracy if latest_loc else None,
        "location_history": _location_history(locations),
        "active_vehicle": vehicle,
        "active_shipment": active_shipment,
        "mode": "demo" if driver.is_demo else "live",
        "is_mock": bool(driver.is_demo),
        "last_updated": driver.updated_at.isoformat() if driver.updated_at else datetime.now(timezone.utc).isoformat(),
    }


async def get_driver_tracking_full(db: AsyncSession, driver_id_or_code: str) -> Dict[str, Any]:
    driver = await get_driver_by_id(db, driver_id_or_code)
    if not driver:
        raise AppException(
            message=f"Driver '{driver_id_or_code}' not found.",
            code="DRIVER_NOT_FOUND",
            status_code=404,
        )

    vehicle = await get_vehicle_by_id(db, driver.active_vehicle_id) if driver.active_vehicle_id else None

    result = await db.execute(
        select(Shipment).where(
            Shipment.assigned_driver_id == driver.id,
            Shipment.status.in_(ACTIVE_RUN_STATUSES),
        )
    )
    active_shipment = result.scalars().first()

    loc_res = await db.execute(
        select(DriverLocation)
        .where(DriverLocation.driver_id == driver.id)
        .order_by(desc(DriverLocation.recorded_at))
        .limit(LOCATIONS_PER_DRIVER_LIMIT)
    )
    return _driver_tracking_payload(driver, vehicle, active_shipment, list(loc_res.scalars().all()))


async def get_drivers_tracking_bulk(db: AsyncSession, drivers: List[Driver]) -> List[Dict[str, Any]]:
    """
    Tracking payloads for many drivers using batched queries.

    The previous implementation issued four extra queries per driver
    (1 + 4N round trips). Note: do NOT replace this with lazy relationship
    access — under async SQLAlchemy that raises MissingGreenlet.
    """
    if not drivers:
        return []

    driver_pks = [d.id for d in drivers]
    vehicle_ids = [d.active_vehicle_id for d in drivers if d.active_vehicle_id]

    vehicles: Dict[str, Vehicle] = {}
    if vehicle_ids:
        veh_res = await db.execute(select(Vehicle).where(Vehicle.id.in_(vehicle_ids)))
        vehicles = {v.id: v for v in veh_res.scalars().all()}

    shipments: Dict[str, Shipment] = {}
    ship_res = await db.execute(
        select(Shipment).where(
            Shipment.assigned_driver_id.in_(driver_pks),
            Shipment.status.in_(ACTIVE_RUN_STATUSES),
        )
    )
    for shipment in ship_res.scalars().all():
        shipments.setdefault(shipment.assigned_driver_id, shipment)

    locations: Dict[str, List[DriverLocation]] = {}
    loc_res = await db.execute(
        select(DriverLocation)
        .where(DriverLocation.driver_id.in_(driver_pks))
        .order_by(desc(DriverLocation.recorded_at))
    )
    for loc in loc_res.scalars().all():
        bucket = locations.setdefault(loc.driver_id, [])
        if len(bucket) < LOCATIONS_PER_DRIVER_LIMIT:
            bucket.append(loc)

    return [
        _driver_tracking_payload(
            driver,
            vehicles.get(driver.active_vehicle_id) if driver.active_vehicle_id else None,
            shipments.get(driver.id),
            locations.get(driver.id, []),
        )
        for driver in drivers
    ]


async def record_tracking_event(
    db: AsyncSession,
    tracking_id: str,
    status: str,
    location: str,
    message: str,
    event_type: str = "LOCATION_UPDATE",
    mode: Optional[str] = None,
    is_mock: Optional[bool] = None,
    actor: str = "tracking_system",
) -> ShipmentEvent:
    """
    Record a tracking update.

    Delegates the status write to the shipment service so the state machine and
    the delivery-date handling are enforced on this path too. Previously this
    was a second, unguarded status writer that could mark a shipment DELIVERED
    without recording a delivery date.
    """
    shipment = await get_shipment_by_id_or_tracking(db, tracking_id)
    if not shipment:
        raise AppException(
            message=f"Shipment '{tracking_id}' not found.",
            code="SHIPMENT_NOT_FOUND",
            status_code=404,
        )

    old_status = shipment.status
    target_status = (status or old_status).strip().upper()

    if target_status != old_status:
        await update_shipment_status(
            db,
            shipment.tracking_id,
            target_status,
            location=location,
            message=message,
            actor=actor,
        )
        # update_shipment_status already persisted an event + audit record.
        events = await get_shipment_events_for_shipment(db, shipment, limit=1)
        if events:
            return events[-1]
        refreshed = await get_shipment_by_id_or_tracking(db, shipment.tracking_id)
        shipment = refreshed or shipment

    derived_mock = bool(shipment.is_demo) if is_mock is None else bool(is_mock)
    derived_mode = mode or ("demo" if derived_mock else "live")

    event = ShipmentEvent(
        id=str(uuid.uuid4()),
        shipment_id=shipment.id,
        tracking_id=shipment.tracking_id,
        event_type=event_type,
        status=shipment.status,
        location=location,
        message=message,
        source="travelogix_ops",
        mode=derived_mode,
        is_mock=derived_mock,
        is_demo=bool(shipment.is_demo),
        timestamp=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)

    if location:
        shipment.current_location = location
        shipment.updated_at = datetime.now(timezone.utc)

    await create_audit_log(
        db=db,
        actor=actor,
        action="TRACKING_EVENT_RECORDED",
        entity_type="SHIPMENT",
        entity_id=shipment.tracking_id,
        description=f"Tracking event for {shipment.tracking_id}: {shipment.status} at {location}",
        metadata={"location": location, "status": shipment.status, "message": message, "old_status": old_status},
        is_demo=derived_mock,
    )
    await db.commit()
    await db.refresh(event)

    try:
        from app.realtime.manager import manager as realtime_manager

        await realtime_manager.broadcast_to_channel(
            f"tracking:{shipment.tracking_id}",
            {
                "event": "shipment.status_changed" if old_status != shipment.status else "shipment.location_changed",
                "tracking_id": shipment.tracking_id,
                "status": shipment.status,
                "location": location,
                "message": message,
                "mode": derived_mode,
                "is_mock": derived_mock,
                "timestamp": event.timestamp.isoformat(),
            },
        )
        await realtime_manager.broadcast_to_channel(
            "admin:all",
            {
                "event": "shipment.location_changed",
                "tracking_id": shipment.tracking_id,
                "status": shipment.status,
                "location": location,
                "timestamp": event.timestamp.isoformat(),
            },
        )
    except Exception as exc:  # pragma: no cover - telemetry is not critical
        logger.warning(f"Realtime tracking broadcast skipped: {exc}")

    return event
