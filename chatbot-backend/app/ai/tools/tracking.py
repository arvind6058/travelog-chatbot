"""
Shipment tracking/registration tools.

Tracking reads the Travelogix database only. There is no driver-GPS or carrier
telemetry integration here, so every field returned is either a persisted column
or an explicit "not available" - never an invented milestone.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy import select, or_

from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.audit_log import AuditLog  # noqa: F401  (re-exported for callers)
from app.models.user import User  # noqa: F401  (re-exported for callers)

NO_EVENTS_MESSAGE = "No scanned milestones are recorded for this shipment yet."


async def trackShipmentAsync(tracking_id: str, db) -> Dict[str, Any]:
    """
    Retrieve verified shipment tracking events from the database.

    One query for the shipment plus exactly one query each for the event timeline,
    the assigned driver and the assigned vehicle - the ORM models expose no
    relationships, so eager loading is not available, but the previous version
    re-selected the shipment row for every related lookup.
    """
    clean_id = tracking_id.strip().upper() if tracking_id else ""
    if not clean_id:
        return {
            "tracking_id": None,
            "found": False,
            "status": "NO_TRACKING_ID",
            "message": "No tracking ID was supplied.",
            "verified_location": None,
            "events": [],
            "provenance": {
                "source": "travelogix_database",
                "mode": "unavailable",
                "is_mock": False,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    stmt = select(Shipment).where(
        or_(Shipment.tracking_id == clean_id, Shipment.id == clean_id)
    )
    res = await db.execute(stmt)
    shipment = res.scalar_one_or_none()

    if not shipment:
        return {
            "tracking_id": clean_id,
            "found": False,
            "status": "NOT_FOUND",
            "message": f"Shipment '{clean_id}' was not found in the Travelogix database.",
            "verified_location": None,
            "events": [],
            "provenance": {
                "source": "travelogix_database",
                "mode": "live",
                "is_mock": False,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    event_res = await db.execute(
        select(ShipmentEvent)
        .where(ShipmentEvent.shipment_id == shipment.id)
        .order_by(ShipmentEvent.timestamp.asc())
    )
    events = list(event_res.scalars().all())

    event_list = [
        {
            "status": e.status,
            "location": e.location,
            "message": e.message,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        for e in events
    ]

    driver_info = None
    if shipment.assigned_driver_id:
        from app.models.driver import Driver
        d_res = await db.execute(select(Driver).where(Driver.id == shipment.assigned_driver_id))
        drv = d_res.scalar_one_or_none()
        if drv:
            driver_info = {
                "id": drv.id,
                "driver_id": drv.driver_id,
                "full_name": drv.full_name,
                "phone": drv.phone,
            }

    vehicle_info = None
    if shipment.assigned_vehicle_id:
        from app.models.vehicle import Vehicle
        v_res = await db.execute(select(Vehicle).where(Vehicle.id == shipment.assigned_vehicle_id))
        veh = v_res.scalar_one_or_none()
        if veh:
            vehicle_info = {
                "id": veh.id,
                "registration_number": veh.registration_number,
                "model": veh.model,
            }

    last_updated = (
        shipment.updated_at.isoformat() if shipment.updated_at
        else (shipment.created_at.isoformat() if shipment.created_at else None)
    )

    verified_location = shipment.current_location or shipment.origin

    return {
        "tracking_id": shipment.tracking_id,
        "found": True,
        "status": shipment.status,
        "origin": shipment.origin,
        "destination": shipment.destination,
        "customer_name": shipment.customer_name,
        "customer_email": shipment.customer_email,
        "shipper_name": shipment.shipper_name,
        "recipient_name": shipment.recipient_name,
        "package_name": shipment.package_name,
        "weight_kg": float(shipment.weight_kg) if shipment.weight_kg is not None else None,
        "pickup_date": shipment.pickup_date,
        "expected_delivery_date": shipment.expected_delivery_date,
        "cost_inr": float(shipment.cost_inr) if shipment.cost_inr is not None else None,
        "verified_location": verified_location,
        "current_location": verified_location,
        "driver": driver_info,
        "vehicle": vehicle_info,
        "last_updated": last_updated,
        "message": f"Shipment status is '{shipment.status}' at {verified_location}.",
        "events": event_list,
        "events_note": None if event_list else NO_EVENTS_MESSAGE,
        "provenance": {
            "source": "travelogix_database",
            "mode": "demo" if shipment.is_demo else "latest_stored",
            "is_mock": bool(shipment.is_demo),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def trackShipment(tracking_id: str, db=None) -> Dict[str, Any]:
    """
    Synchronous fallback: queries travelogix.db directly via SQLite if no async session is attached.
    """
    clean_id = tracking_id.strip().upper() if tracking_id else ""
    if not clean_id:
        return {
            "tracking_id": None,
            "found": False,
            "status": "NO_TRACKING_ID",
            "message": "No tracking ID was supplied.",
            "verified_location": None,
            "events": [],
            "provenance": {
                "source": "travelogix_database",
                "mode": "unavailable",
                "is_mock": False,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    try:
        import os
        import sqlite3

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        db_path = os.path.join(base_dir, "travelogix.db")
        if not os.path.exists(db_path):
            db_path = "travelogix.db"

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM shipments WHERE UPPER(tracking_id) = ? OR UPPER(id) = ?",
            (clean_id, clean_id),
        )
        row = c.fetchone()
        if not row:
            conn.close()
            return {
                "tracking_id": clean_id,
                "found": False,
                "status": "NOT_FOUND",
                "message": f"Shipment '{clean_id}' was not found in the Travelogix database.",
                "verified_location": None,
                "events": [],
                "provenance": {
                    "source": "travelogix_database",
                    "mode": "json",
                    "is_mock": False,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                },
            }

        shipment_dict = dict(row)
        shipment_id = shipment_dict["id"]

        c.execute(
            "SELECT status, location, message, timestamp FROM shipment_events WHERE shipment_id = ? ORDER BY timestamp ASC",
            (shipment_id,),
        )
        events = [dict(r) for r in c.fetchall()]

        driver_info = None
        if shipment_dict.get("assigned_driver_id"):
            c.execute(
                "SELECT id, driver_id, full_name, phone FROM drivers WHERE id = ? OR driver_id = ?",
                (shipment_dict["assigned_driver_id"], shipment_dict["assigned_driver_id"]),
            )
            d_row = c.fetchone()
            if d_row:
                driver_info = dict(d_row)

        vehicle_info = None
        if shipment_dict.get("assigned_vehicle_id"):
            c.execute(
                "SELECT id, registration_number, model FROM vehicles WHERE id = ?",
                (shipment_dict["assigned_vehicle_id"],),
            )
            v_row = c.fetchone()
            if v_row:
                vehicle_info = dict(v_row)

        conn.close()

        last_updated = shipment_dict.get("updated_at") or shipment_dict.get("created_at") or datetime.now(timezone.utc).isoformat()
        verified_location = shipment_dict.get("current_location") or shipment_dict.get("origin")
        is_demo = bool(shipment_dict.get("is_demo"))

        return {
            "tracking_id": shipment_dict["tracking_id"],
            "found": True,
            "status": shipment_dict["status"],
            "origin": shipment_dict["origin"],
            "destination": shipment_dict["destination"],
            "customer_name": shipment_dict.get("customer_name"),
            "customer_email": shipment_dict.get("customer_email"),
            "shipper_name": shipment_dict.get("shipper_name"),
            "recipient_name": shipment_dict.get("recipient_name"),
            "package_name": shipment_dict.get("package_name"),
            "weight_kg": float(shipment_dict["weight_kg"]) if shipment_dict.get("weight_kg") is not None else None,
            "pickup_date": shipment_dict.get("pickup_date"),
            "expected_delivery_date": shipment_dict.get("expected_delivery_date"),
            "cost_inr": float(shipment_dict["cost_inr"]) if shipment_dict.get("cost_inr") is not None else None,
            "verified_location": verified_location,
            "current_location": verified_location,
            "driver": driver_info,
            "vehicle": vehicle_info,
            "last_updated": str(last_updated),
            "message": f"Shipment status is '{shipment_dict['status']}' at {verified_location}.",
            "events": events,
            "events_note": None if events else NO_EVENTS_MESSAGE,
            "provenance": {
                "source": "travelogix_database",
                "mode": "demo" if is_demo else "latest_stored",
                "is_mock": is_demo,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    except Exception as exc:
        return {
            "tracking_id": clean_id,
            "found": False,
            "status": "UNAVAILABLE",
            "message": f"Error retrieving tracking info for '{clean_id}': {exc}",
            "verified_location": None,
            "events": [],
            "provenance": {
                "source": "travelogix_database",
                "mode": "unavailable",
                "is_mock": False,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
        }


async def registerShipmentAsync(
    db,
    origin: str,
    destination: str,
    weight_kg: float,
    recipient_name: str,
    package_type: str = "Standard Parcel",
    customer_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
    delivery_type: str = "Standard Road Freight",
) -> Dict[str, Any]:
    """
    Create a new shipment record via shipment_service.

    `recipient_name`, `customer_name` and `customer_email` are deliberately
    required: chat-created shipments used to be persisted as "Customer" /
    "customer@example.com", which fabricated an identity. Identity no longer has a
    placeholder default here and the caller must supply the real one.
    """
    from app.services import shipment_service

    if not customer_email:
        raise ValueError("customer_email is required to register a shipment")
    if not customer_name:
        raise ValueError("customer_name is required to register a shipment")

    shipment = await shipment_service.create_shipment(
        db=db,
        data={
            "customer_id": customer_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "shipper_name": f"{origin} Logistics Hub",
            "recipient_name": recipient_name,
            "package_name": f"{weight_kg}kg {package_type}",
            "delivery_type": delivery_type,
            "origin": origin,
            "destination": destination,
            "weight_kg": weight_kg,
            "cost_inr": 0.0,  # shipment_service auto-calculates cost from weight/route
            "pickup_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "expected_delivery_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        },
        actor=customer_email,
    )

    return {
        "success": True,
        "tracking_id": shipment.tracking_id,
        "origin": shipment.origin,
        "destination": shipment.destination,
        "weight_kg": float(shipment.weight_kg) if shipment.weight_kg is not None else None,
        "recipient_name": shipment.recipient_name,
        "customer_name": shipment.customer_name,
        "customer_email": shipment.customer_email,
        "status": shipment.status,
        "cost_inr": float(shipment.cost_inr) if shipment.cost_inr is not None else None,
        "provenance": {
            "source": "travelogix_database",
            "mode": "live",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "is_mock": False,
        },
    }


async def getDriverInfoAsync(tracking_id: Optional[str], db) -> Dict[str, Any]:
    if tracking_id:
        shipment_data = await trackShipmentAsync(tracking_id, db)
        driver = shipment_data.get("driver")
        if driver:
            return {
                "found": True,
                "driver": driver,
                "assigned_shipment": tracking_id,
                "status": "Assigned & Active",
                "provenance": shipment_data.get("provenance"),
            }
    return {
        "found": False,
        "message": "No driver assigned or details unavailable for this shipment.",
        "provenance": {
            "source": "travelogix_database",
            "mode": "live",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "is_mock": False,
        },
    }


async def getVehicleStatusAsync(tracking_id: Optional[str], db) -> Dict[str, Any]:
    if tracking_id:
        shipment_data = await trackShipmentAsync(tracking_id, db)
        vehicle = shipment_data.get("vehicle")
        if vehicle:
            return {
                "found": True,
                "vehicle": vehicle,
                "assigned_shipment": tracking_id,
                "status": "In Transit",
                "current_location": shipment_data.get("verified_location"),
                "provenance": shipment_data.get("provenance"),
            }
    return {
        "found": False,
        "message": "No vehicle assigned or details unavailable for this shipment.",
        "provenance": {
            "source": "travelogix_database",
            "mode": "live",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "is_mock": False,
        },
    }

