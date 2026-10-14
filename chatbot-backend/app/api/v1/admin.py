"""
Admin (logistics console) API.

Every route in this module requires an authenticated administrator. The router
itself carries the dependency, so a new endpoint cannot accidentally be added
without authorisation — previously *no* route here had any guard at all and the
whole console, including customer transcripts and driver PII, was readable and
writable by an anonymous caller.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.models.audit_log import AuditLog
from app.models.conversation import Conversation
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.user import User
from app.models.vehicle import Vehicle
from app.realtime.manager import manager as realtime_manager
from app.schemas.admin import (
    AssignmentCreate,
    DriverLocationCreate,
    ShipmentStatusUpdate,
    TrackingEventCreate,
)
from app.services import (
    assignment_service,
    audit_service,
    conversation_service,
    driver_service,
    shipment_service,
    tracking_service,
    vehicle_service,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin Operations"],
    dependencies=[Depends(require_admin)],
)

# Statuses counted on the dashboard.
DASHBOARD_STATUSES = (
    "REGISTERED",
    "PICKUP_SCHEDULED",
    "PICKED_UP",
    "IN_TRANSIT",
    "ARRIVED_AT_HUB",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
    "DELAYED",
    "FAILED_DELIVERY",
    "CANCELLED",
)

PAGE_LIMIT = Query(50, ge=1, le=200)
PAGE_OFFSET = Query(0, ge=0)


def _shipment_row(s: Shipment) -> Dict[str, Any]:
    return {
        "id": s.id,
        "tracking_id": s.tracking_id,
        "customer_name": s.customer_name,
        "customer_email": s.customer_email,
        "shipper_name": s.shipper_name,
        "recipient_name": s.recipient_name,
        "origin": s.origin,
        "destination": s.destination,
        "delivery_type": s.delivery_type,
        "package_name": s.package_name,
        "weight_kg": float(s.weight_kg) if s.weight_kg is not None else None,
        "dimensions": s.dimensions,
        "pickup_date": s.pickup_date,
        "expected_delivery_date": s.expected_delivery_date,
        "cost_inr": float(s.cost_inr) if s.cost_inr is not None else None,
        "status": s.status,
        "current_location": s.current_location,
        "assigned_driver_id": s.assigned_driver_id,
        "assigned_vehicle_id": s.assigned_vehicle_id,
        "is_demo": bool(s.is_demo),
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _driver_row(d: Driver) -> Dict[str, Any]:
    """
    Explicit projection.

    Driver rows used to be returned as raw ORM objects, which FastAPI's encoder
    expands via ``vars()`` — publishing masked_aadhaar, license_number,
    date_of_birth and pin to the caller (and any column added later).
    """
    return {
        "id": d.id,
        "driver_id": d.driver_id,
        "full_name": d.full_name,
        "phone": d.phone,
        "email": d.email,
        "city": d.city,
        "state": d.state,
        "kyc_status": d.kyc_status,
        "license_number": d.license_number,
        "license_status": d.license_status,
        "status": d.status,
        "base_location": d.base_location,
        "service_area": d.service_area,
        "current_location": d.current_location,
        "active_vehicle_id": d.active_vehicle_id,
        "is_demo": bool(d.is_demo),
    }


def _vehicle_row(v: Vehicle) -> Dict[str, Any]:
    return {
        "id": v.id,
        "vehicle_id": v.vehicle_id,
        "registration_number": v.registration_number,
        "vehicle_type": v.vehicle_type,
        "model": v.model,
        "capacity": v.capacity,
        "fuel_type": v.fuel_type,
        "status": v.status,
        "rc_status": v.rc_status,
        "insurance_status": v.insurance_status,
        "puc_status": v.puc_status,
        "fitness_status": v.fitness_status,
        "permit_status": v.permit_status,
        "current_driver_id": v.current_driver_id,
        "is_demo": bool(v.is_demo),
    }


def _event_row(e: ShipmentEvent) -> Dict[str, Any]:
    return {
        "id": e.id,
        "tracking_id": e.tracking_id,
        "event_type": e.event_type,
        "status": e.status,
        "location": e.location,
        "message": e.message,
        "mode": e.mode,
        "is_mock": bool(e.is_mock),
        "is_demo": bool(e.is_demo),
        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
    }


async def _broadcast(channel: str, payload: Dict[str, Any]) -> None:
    """Telemetry must never break a successful write."""
    try:
        await realtime_manager.broadcast_to_channel(channel, payload)
    except Exception:
        pass


# ============================================================
# DASHBOARD
# ============================================================
@router.get("/dashboard", summary="Admin Operations Dashboard Metrics")
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db_session)):
    # One aggregate instead of eleven COUNT round trips.
    status_counts = (
        await db.execute(
            select(
                *[
                    func.count(case((Shipment.status == status_name, 1))).label(status_name)
                    for status_name in DASHBOARD_STATUSES
                ]
            ).select_from(Shipment)
        )
    ).one()
    metrics_by_status = dict(zip(DASHBOARD_STATUSES, status_counts))

    driver_counts = (
        await db.execute(
            select(
                func.count(Driver.id).filter(Driver.status == "AVAILABLE"),
                func.count(Driver.id).filter(Driver.status == "ON_DELIVERY"),
            )
        )
    ).one()

    vehicle_active = (
        await db.execute(
            select(func.count(Vehicle.id)).where(Vehicle.status.in_(["ACTIVE", "IN_TRANSIT"]))
        )
    ).scalar_one()

    customer_count = (
        await db.execute(select(func.count(User.id)).where(User.role == "CUSTOMER"))
    ).scalar_one()
    total_conversations = (await db.execute(select(func.count(Conversation.id)))).scalar_one()

    # Ten rows, not the whole table sliced in Python.
    recent_shipments_db = await shipment_service.get_all_shipments(db, limit=10)
    recent_shipments = [
        {
            "id": s.id,
            "trackingId": s.tracking_id,
            "customer": s.customer_name,
            "origin": s.origin,
            "destination": s.destination,
            "status": s.status,
            "deliveryType": s.delivery_type,
            "cost": float(s.cost_inr) if s.cost_inr is not None else None,
            "createdAt": s.created_at.isoformat() if s.created_at else None,
        }
        for s in recent_shipments_db
    ]

    recent_events_db = (
        await db.execute(
            select(ShipmentEvent).order_by(desc(ShipmentEvent.created_at)).limit(10)
        )
    ).scalars().all()
    recent_events = [
        {
            "id": e.id,
            "trackingId": e.tracking_id,
            "title": f"{e.event_type}: {e.message}",
            "status": e.status,
            "location": e.location,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        for e in recent_events_db
    ]

    total_shipments = (
        await db.execute(select(func.count(Shipment.id)))
    ).scalar_one()

    return {
        "success": True,
        "metrics": {
            "totalShipments": total_shipments,
            "registered": metrics_by_status.get("REGISTERED", 0),
            "inTransit": metrics_by_status.get("IN_TRANSIT", 0),
            "outForDelivery": metrics_by_status.get("OUT_FOR_DELIVERY", 0),
            "delivered": metrics_by_status.get("DELIVERED", 0),
            "delayed": metrics_by_status.get("DELAYED", 0),
            "availableDrivers": driver_counts[0],
            "driversOnDelivery": driver_counts[1],
            "activeVehicles": vehicle_active,
            "customerCount": customer_count,
            "totalConversations": total_conversations,
        },
        "recentShipments": recent_shipments,
        "recentEvents": recent_events,
    }


# ============================================================
# SHIPMENTS
# ============================================================
async def _shipments_payload(db: AsyncSession, limit: int, offset: int) -> Dict[str, Any]:
    shipments = await shipment_service.get_all_shipments(db, limit=limit, offset=offset)
    total = await shipment_service.count_shipments(db)
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "shipments": [_shipment_row(s) for s in shipments],
    }


@router.get("/shipments", summary="Get all registered shipments")
async def get_shipments(
    limit: int = PAGE_LIMIT,
    offset: int = PAGE_OFFSET,
    db: AsyncSession = Depends(get_db_session),
):
    return await _shipments_payload(db, limit, offset)


@router.post("/shipments", summary="Register new shipment")
async def create_shipment(
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db_session),
    admin: Dict[str, Any] = Depends(require_admin),
):
    # Admins may register on behalf of a customer, but the operation is audited
    # against the administrator, never a client-supplied actor.
    shipment = await shipment_service.create_shipment(
        db, payload, actor=str(admin.get("email"))
    )
    await _broadcast(
        f"tracking:{shipment.tracking_id}",
        {"event": "shipment.registered", "tracking_id": shipment.tracking_id, "status": shipment.status},
    )
    return {
        "success": True,
        "message": "Shipment registered successfully.",
        "shipment": _shipment_row(shipment),
    }


@router.get("/shipments/{tracking_id_or_id}", summary="Get detailed shipment information")
async def get_shipment_detail(tracking_id_or_id: str, db: AsyncSession = Depends(get_db_session)):
    tracking_full = await tracking_service.get_shipment_tracking_full(db, tracking_id_or_id)
    return {
        "success": True,
        "shipment": _shipment_row(tracking_full["shipment"]),
        "driver": _driver_row(tracking_full["driver"]) if tracking_full.get("driver") else None,
        "vehicle": _vehicle_row(tracking_full["vehicle"]) if tracking_full.get("vehicle") else None,
        "events": [_event_row(e) for e in tracking_full.get("events", [])],
    }


@router.patch("/shipments/{tracking_id_or_id}", summary="Update shipment status")
async def update_shipment(
    tracking_id_or_id: str,
    payload: ShipmentStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    admin: Dict[str, Any] = Depends(require_admin),
):
    shipment = await shipment_service.update_shipment_status(
        db,
        tracking_id_or_id,
        new_status=payload.status,
        location=payload.location,
        message=payload.message,
        actor=str(admin.get("email")),
    )
    await _broadcast(
        f"tracking:{shipment.tracking_id}",
        {
            "event": "shipment.status_changed",
            "tracking_id": shipment.tracking_id,
            "status": shipment.status,
            "location": shipment.current_location,
        },
    )
    return {
        "success": True,
        "message": "Shipment updated successfully.",
        "shipment": {
            "id": shipment.id,
            "tracking_id": shipment.tracking_id,
            "status": shipment.status,
            "current_location": shipment.current_location,
            "actual_delivery_date": shipment.actual_delivery_date,
        },
    }


# ============================================================
# DRIVERS
# ============================================================
@router.get("/drivers", summary="List all drivers")
async def get_drivers(
    limit: int = PAGE_LIMIT,
    offset: int = PAGE_OFFSET,
    db: AsyncSession = Depends(get_db_session),
):
    drivers = await driver_service.get_all_drivers(db, limit=limit, offset=offset)
    return {"success": True, "drivers": [_driver_row(d) for d in drivers]}


@router.get("/drivers/eligible", summary="Get drivers eligible for assignment")
async def get_eligible_drivers(db: AsyncSession = Depends(get_db_session)):
    drivers = await driver_service.get_eligible_drivers(db)
    return {
        "success": True,
        "drivers": [
            {
                "id": d.id,
                "driver_id": d.driver_id,
                "full_name": d.full_name,
                "phone": d.phone,
                "license_status": d.license_status,
                "status": d.status,
                "active_vehicle_id": d.active_vehicle_id,
            }
            for d in drivers
        ],
    }


@router.post("/drivers", summary="Create new driver")
async def create_driver(
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db_session),
    admin: Dict[str, Any] = Depends(require_admin),
):
    driver = await driver_service.create_driver(db, payload, actor=str(admin.get("email")))
    return {
        "success": True,
        "message": "Driver created successfully.",
        "driver": {
            "id": driver.id,
            "driver_id": driver.driver_id,
            "full_name": driver.full_name,
            "status": driver.status,
        },
    }


@router.get("/drivers/{driver_id_or_uuid}", summary="Get driver details")
async def get_driver_detail(driver_id_or_uuid: str, db: AsyncSession = Depends(get_db_session)):
    driver_full = await tracking_service.get_driver_tracking_full(db, driver_id_or_uuid)
    return {
        "success": True,
        "driver": {
            **_driver_row(driver_full["driver"]),
            "latitude": driver_full.get("latitude"),
            "longitude": driver_full.get("longitude"),
            "accuracy": driver_full.get("accuracy"),
            "location_history": driver_full.get("location_history", []),
            "active_vehicle": _vehicle_row(driver_full["active_vehicle"])
            if driver_full.get("active_vehicle")
            else None,
            "active_shipment": _shipment_row(driver_full["active_shipment"])
            if driver_full.get("active_shipment")
            else None,
            "mode": driver_full.get("mode"),
            "is_mock": driver_full.get("is_mock"),
            "last_updated": driver_full.get("last_updated"),
        },
    }


@router.patch("/drivers/{driver_id_or_uuid}", summary="Update driver details")
async def update_driver(
    driver_id_or_uuid: str,
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db_session),
    admin: Dict[str, Any] = Depends(require_admin),
):
    driver = await driver_service.update_driver(
        db, driver_id_or_uuid, payload, actor=str(admin.get("email"))
    )
    return {"success": True, "message": "Driver updated successfully.", "driver_id": driver.driver_id}


# ============================================================
# VEHICLES
# ============================================================
@router.get("/vehicles", summary="List all vehicles")
async def get_vehicles(
    limit: int = PAGE_LIMIT,
    offset: int = PAGE_OFFSET,
    db: AsyncSession = Depends(get_db_session),
):
    vehicles = await vehicle_service.get_all_vehicles(db, limit=limit, offset=offset)
    return {"success": True, "vehicles": [_vehicle_row(v) for v in vehicles]}


@router.post("/vehicles", summary="Create new vehicle")
async def create_vehicle(
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db_session),
    admin: Dict[str, Any] = Depends(require_admin),
):
    vehicle = await vehicle_service.create_vehicle(db, payload, actor=str(admin.get("email")))
    return {
        "success": True,
        "message": "Vehicle created successfully.",
        "vehicle": _vehicle_row(vehicle),
    }


@router.get("/vehicles/{vehicle_id_or_reg}", summary="Get vehicle detail")
async def get_vehicle_detail(vehicle_id_or_reg: str, db: AsyncSession = Depends(get_db_session)):
    vehicle = await vehicle_service.get_vehicle_by_id(db, vehicle_id_or_reg)
    if vehicle is None:
        raise AppException(
            message=f"Vehicle '{vehicle_id_or_reg}' not found.",
            code="VEHICLE_NOT_FOUND",
            status_code=404,
        )
    return {"success": True, "vehicle": _vehicle_row(vehicle)}


@router.patch("/vehicles/{vehicle_id_or_reg}", summary="Update vehicle")
async def update_vehicle(
    vehicle_id_or_reg: str,
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db_session),
    admin: Dict[str, Any] = Depends(require_admin),
):
    vehicle = await vehicle_service.update_vehicle(
        db, vehicle_id_or_reg, payload, actor=str(admin.get("email"))
    )
    return {
        "success": True,
        "message": "Vehicle updated successfully.",
        "registration_number": vehicle.registration_number,
    }


# ============================================================
# ASSIGNMENTS
# ============================================================
@router.post("/assignments", summary="Assign shipment to driver and vehicle")
async def create_assignment(
    payload: AssignmentCreate,
    db: AsyncSession = Depends(get_db_session),
    admin: Dict[str, Any] = Depends(require_admin),
):
    assignment = await assignment_service.assign_driver_and_vehicle(
        db=db,
        shipment_id_or_tracking=payload.shipment_id,
        driver_id_or_code=payload.driver_id,
        vehicle_id_or_reg=payload.vehicle_id,
        assigned_by=str(admin.get("email")),
        notes=payload.notes,
    )
    return {
        "success": True,
        "message": "Driver and vehicle assigned to shipment successfully.",
        "assignment_id": assignment.id,
    }


# ============================================================
# TRACKING (SHIPMENT & DRIVER)
# ============================================================
@router.get("/tracking/shipments", summary="List all trackable shipments")
async def get_trackable_shipments(
    limit: int = PAGE_LIMIT,
    offset: int = PAGE_OFFSET,
    db: AsyncSession = Depends(get_db_session),
):
    return await _shipments_payload(db, limit, offset)


@router.get("/tracking/shipments/{tracking_id}", summary="Tracking view for one shipment")
async def get_shipment_tracking(tracking_id: str, db: AsyncSession = Depends(get_db_session)):
    tracking_full = await tracking_service.get_shipment_tracking_full(db, tracking_id)
    return {
        "success": True,
        "tracking": {
            "tracking_id": tracking_full["tracking_id"],
            "status": tracking_full["status"],
            "current_location": tracking_full["current_location"],
            "current_coordinates": tracking_full.get("current_coordinates"),
            "origin": tracking_full["origin"],
            "destination": tracking_full["destination"],
            "route_points": tracking_full.get("route_points", []),
            "expected_delivery_date": tracking_full.get("expected_delivery_date"),
            "driver": _driver_row(tracking_full["driver"]) if tracking_full.get("driver") else None,
            "vehicle": _vehicle_row(tracking_full["vehicle"]) if tracking_full.get("vehicle") else None,
            "events": [_event_row(e) for e in tracking_full.get("events", [])],
            "mode": tracking_full.get("mode"),
            "is_mock": tracking_full.get("is_mock"),
            "source": tracking_full.get("source"),
            "last_updated": tracking_full.get("last_updated"),
        },
    }


@router.get("/tracking/drivers", summary="Live tracking payload for every driver")
async def get_trackable_drivers(
    limit: int = PAGE_LIMIT,
    offset: int = PAGE_OFFSET,
    db: AsyncSession = Depends(get_db_session),
):
    drivers = await driver_service.get_all_drivers(db, limit=limit, offset=offset)
    # Batched: this used to issue four extra queries per driver.
    payloads = await tracking_service.get_drivers_tracking_bulk(db, drivers)
    return {"success": True, "drivers": payloads, "count": len(payloads)}


@router.get("/tracking/drivers/{driver_id}", summary="Tracking view for one driver")
async def get_driver_tracking(driver_id: str, db: AsyncSession = Depends(get_db_session)):
    driver_full = await tracking_service.get_driver_tracking_full(db, driver_id)
    return {"success": True, "tracking": driver_full}


@router.post("/tracking/events", summary="Record a shipment tracking event")
async def record_tracking_event(
    payload: TrackingEventCreate,
    db: AsyncSession = Depends(get_db_session),
    admin: Dict[str, Any] = Depends(require_admin),
):
    event = await tracking_service.record_tracking_event(
        db,
        tracking_id=payload.tracking_id,
        status=payload.status,
        location=payload.location,
        message=payload.message,
        event_type=payload.event_type,
        actor=str(admin.get("email")),
    )
    await _broadcast(
        f"tracking:{event.tracking_id}",
        {
            "event": "shipment.location_changed",
            "tracking_id": event.tracking_id,
            "status": event.status,
            "location": event.location,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        },
    )
    return {"success": True, "message": "Tracking event recorded.", "event": _event_row(event)}


@router.post("/tracking/driver-locations", summary="Record a driver location update")
async def record_driver_location_event(
    payload: DriverLocationCreate,
    db: AsyncSession = Depends(get_db_session),
    admin: Dict[str, Any] = Depends(require_admin),
):
    location = await driver_service.record_driver_location(
        db,
        driver_id_or_code=payload.driver_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        location_name=payload.location_name,
        vehicle_id=payload.vehicle_id,
        shipment_id=payload.shipment_id,
        source=payload.source,
        actor=str(admin.get("email")),
    )
    return {
        "success": True,
        "message": "Driver location recorded successfully.",
        "location_id": location.id,
        "mode": location.mode,
        "is_mock": bool(location.is_mock),
    }


# ============================================================
# CUSTOMERS, CONVERSATIONS, DELAYED, DELIVERED, REPORTS, AUDIT LOGS
# ============================================================
@router.get("/customers", summary="List registered customers")
async def get_customers(
    limit: int = PAGE_LIMIT,
    offset: int = PAGE_OFFSET,
    db: AsyncSession = Depends(get_db_session),
):
    total = (
        await db.execute(select(func.count(User.id)).where(User.role == "CUSTOMER"))
    ).scalar_one()
    result = await db.execute(
        select(User)
        .where(User.role == "CUSTOMER")
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    users = list(result.scalars().all())
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "customers": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "phone": u.phone,
                "status": u.status,
                "is_demo": bool(u.is_demo),
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.get("/conversations", summary="List saved AI Conversations")
async def get_conversations(
    limit: int = PAGE_LIMIT,
    offset: int = PAGE_OFFSET,
    db: AsyncSession = Depends(get_db_session),
):
    conversations = await conversation_service.get_all_conversations(
        db, limit=limit, offset=offset
    )
    return {"success": True, "conversations": conversations, "limit": limit, "offset": offset}


@router.get("/conversations/{conversation_id}", summary="Get detailed AI conversation history")
async def get_conversation_detail(conversation_id: str, db: AsyncSession = Depends(get_db_session)):
    detail = await conversation_service.get_conversation_detail(db, conversation_id)
    return {"success": True, "conversation": detail}


@router.get("/delayed-shipments", summary="Get delayed shipments from DB")
async def get_delayed(
    limit: int = PAGE_LIMIT,
    offset: int = PAGE_OFFSET,
    db: AsyncSession = Depends(get_db_session),
):
    delayed = await shipment_service.get_delayed_shipments(db, limit=limit, offset=offset)
    return {"success": True, "shipments": [_shipment_row(s) for s in delayed]}


@router.get("/delivered", summary="Get delivered shipments from DB")
async def get_delivered(
    limit: int = PAGE_LIMIT,
    offset: int = PAGE_OFFSET,
    db: AsyncSession = Depends(get_db_session),
):
    delivered = await shipment_service.get_delivered_shipments(db, limit=limit, offset=offset)
    return {"success": True, "shipments": [_shipment_row(s) for s in delivered]}


@router.get("/reports", summary="Generate real database analytics reports")
async def get_reports(db: AsyncSession = Depends(get_db_session)):
    total_shipments = (await db.execute(select(func.count(Shipment.id)))).scalar_one()
    delivered = (
        await db.execute(select(func.count(Shipment.id)).where(Shipment.status == "DELIVERED"))
    ).scalar_one()
    delayed = (
        await db.execute(select(func.count(Shipment.id)).where(Shipment.status == "DELAYED"))
    ).scalar_one()
    active_drivers = (
        await db.execute(select(func.count(Driver.id)).where(Driver.status == "ON_DELIVERY"))
    ).scalar_one()

    # On-time means delivered by the promised date, not merely delivered.
    on_time = (
        await db.execute(
            select(func.count(Shipment.id)).where(
                Shipment.status == "DELIVERED",
                Shipment.actual_delivery_date.is_not(None),
                Shipment.actual_delivery_date <= Shipment.expected_delivery_date,
            )
        )
    ).scalar_one()

    return {
        "success": True,
        "summary": {
            "totalShipments": total_shipments,
            "delivered": delivered,
            "delayed": delayed,
            "activeDrivers": active_drivers,
            "deliveryRate": round((delivered / total_shipments) * 100, 1) if total_shipments else 0.0,
            "onTimeDeliveryRate": round((on_time / delivered) * 100, 1) if delivered else 0.0,
        },
    }


@router.get("/audit-logs", summary="List system audit logs")
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
):
    logs = await audit_service.get_audit_logs(db, limit=limit, offset=offset)
    total = await audit_service.count_audit_logs(db)
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "audit_logs": [
            {
                "id": l.id,
                "actor": l.actor,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "description": l.description,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "is_demo": bool(l.is_demo),
            }
            for l in logs
        ],
    }
