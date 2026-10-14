import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import logger
from app.models.assignment import ShipmentDriverAssignment
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.vehicle import Vehicle
from app.services.audit_service import create_audit_log
from app.services.driver_service import get_driver_by_id
from app.services.shipment_service import get_shipment_by_id_or_tracking
from app.services.vehicle_service import get_vehicle_by_id

# Driver statuses that may take new work.
ASSIGNABLE_DRIVER_STATUSES = ("AVAILABLE",)


async def assign_driver_and_vehicle(
    db: AsyncSession,
    shipment_id_or_tracking: str,
    driver_id_or_code: str,
    vehicle_id_or_reg: Optional[str] = None,
    assigned_by: str = "system",
    notes: Optional[str] = None,
) -> ShipmentDriverAssignment:
    """
    Assign a driver (and optionally a vehicle) to a shipment.

    The driver is claimed with a conditional UPDATE so two concurrent requests
    cannot both win the same driver; previously both read status='AVAILABLE'
    and both inserted an ACTIVE assignment.
    """
    shipment = await get_shipment_by_id_or_tracking(db, shipment_id_or_tracking)
    if not shipment:
        raise AppException(
            message=f"Shipment '{shipment_id_or_tracking}' not found.",
            code="SHIPMENT_NOT_FOUND",
            status_code=404,
        )

    driver = await get_driver_by_id(db, driver_id_or_code)
    if not driver:
        raise AppException(
            message=f"Driver '{driver_id_or_code}' not found.",
            code="DRIVER_NOT_FOUND",
            status_code=404,
        )

    if (driver.license_status or "").upper() != "VALID":
        raise AppException(
            message=f"Driver '{driver.full_name}' does not have a valid license.",
            code="DRIVER_NOT_ELIGIBLE",
            status_code=409,
        )

    if (driver.status or "").upper() == "ON_DELIVERY":
        raise AppException(
            message=f"Driver '{driver.full_name}' is already on a delivery.",
            code="DRIVER_NOT_ELIGIBLE",
            status_code=409,
        )

    # Mapped to the driver's primary key: a caller-supplied reference that does
    # not resolve must fail rather than silently produce a vehicle-less run.
    vehicle: Optional[Vehicle] = None
    veh_ref = vehicle_id_or_reg or driver.active_vehicle_id
    if veh_ref:
        vehicle = await get_vehicle_by_id(db, veh_ref)
        if vehicle is None:
            raise AppException(
                message=f"Vehicle '{veh_ref}' not found.",
                code="VEHICLE_NOT_FOUND",
                status_code=404,
            )

    # Atomic claim: only succeeds while the driver is still available.
    claim = await db.execute(
        text(
            "UPDATE drivers SET status = 'ON_DELIVERY' "
            "WHERE id = :driver_pk AND UPPER(COALESCE(status, '')) IN ('AVAILABLE', 'ACTIVE')"
        ),
        {"driver_pk": driver.id},
    )
    if claim.rowcount != 1:
        await db.rollback()
        raise AppException(
            message=f"Driver '{driver.full_name}' is no longer available.",
            code="DRIVER_NOT_ELIGIBLE",
            status_code=409,
        )

    assignment = ShipmentDriverAssignment(
        id=str(uuid.uuid4()),
        shipment_id=shipment.id,
        driver_id=driver.id,
        vehicle_id=vehicle.id if vehicle else None,
        assigned_at=datetime.now(timezone.utc),
        status="ACTIVE",
        assigned_by=assigned_by,
        is_demo=bool(shipment.is_demo),
        notes=notes,
    )
    db.add(assignment)

    shipment.assigned_driver_id = driver.id
    if vehicle:
        shipment.assigned_vehicle_id = vehicle.id

    if shipment.status == "REGISTERED":
        shipment.status = "PICKUP_SCHEDULED"

    if vehicle:
        driver.active_vehicle_id = vehicle.id
        vehicle.status = "IN_TRANSIT"
        # Store the driver's primary key on both sides so the two "current X"
        # columns are joinable (one side used to hold driver.driver_id).
        vehicle.current_driver_id = driver.id

    event_msg = f"Assigned driver {driver.full_name} ({driver.driver_id})"
    if vehicle:
        event_msg += f" with vehicle {vehicle.registration_number}"

    event = ShipmentEvent(
        id=str(uuid.uuid4()),
        shipment_id=shipment.id,
        tracking_id=shipment.tracking_id,
        event_type="DRIVER_ASSIGNED",
        status=shipment.status,
        location=shipment.current_location or shipment.origin,
        message=event_msg,
        source="travelogix_ops",
        mode="demo" if shipment.is_demo else "live",
        is_mock=bool(shipment.is_demo),
        is_demo=bool(shipment.is_demo),
        timestamp=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.flush()

    await create_audit_log(
        db=db,
        actor=assigned_by,
        action="SHIPMENT_DRIVER_ASSIGNED",
        entity_type="SHIPMENT",
        entity_id=shipment.tracking_id,
        description=event_msg,
        metadata={
            "shipment_id": shipment.tracking_id,
            "driver_id": driver.driver_id,
            "vehicle_reg": vehicle.registration_number if vehicle else None,
        },
        is_demo=bool(shipment.is_demo),
    )

    await db.commit()
    await db.refresh(assignment)

    # Realtime publication (best effort: never fails the assignment)
    try:
        from app.realtime.manager import manager as realtime_manager

        event_payload = {
            "event": "driver.assignment.created",
            "tracking_id": shipment.tracking_id,
            "driver_id": driver.driver_id,
            "driver_name": driver.full_name,
            "vehicle_reg": vehicle.registration_number if vehicle else None,
            "status": shipment.status,
            "location": shipment.current_location or shipment.origin,
            "timestamp": event.timestamp.isoformat(),
        }
        await realtime_manager.broadcast_to_channel(f"tracking:{shipment.tracking_id}", event_payload)
        await realtime_manager.broadcast_to_channel(f"drivers:{driver.driver_id}", event_payload)
        await realtime_manager.broadcast_to_channel("admin:all", event_payload)
    except Exception as exc:  # pragma: no cover - telemetry is not critical
        logger.warning(f"Realtime assignment broadcast skipped: {exc}")

    return assignment


async def close_active_assignment(db: AsyncSession, shipment: Shipment) -> None:
    """
    Complete the shipment's ACTIVE assignment and free the fleet resources.

    Nothing ever transitioned an assignment away from ACTIVE, so the table
    accumulated permanently-active rows and drivers stayed busy forever.
    """
    result = await db.execute(
        select(ShipmentDriverAssignment).where(
            ShipmentDriverAssignment.shipment_id == shipment.id,
            ShipmentDriverAssignment.status == "ACTIVE",
        )
    )
    assignments = list(result.scalars().all())

    for assignment in assignments:
        assignment.status = "COMPLETED"
        assignment.unassigned_at = datetime.now(timezone.utc)

        await db.execute(
            update(Driver)
            .where(Driver.id == assignment.driver_id)
            .values(status="AVAILABLE", active_vehicle_id=None)
        )
        if assignment.vehicle_id:
            await db.execute(
                update(Vehicle)
                .where(Vehicle.id == assignment.vehicle_id)
                .values(status="AVAILABLE", current_driver_id=None)
            )
