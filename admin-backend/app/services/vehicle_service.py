import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import logger
from app.models.vehicle import Vehicle
from app.services.audit_service import create_audit_log

EDITABLE_VEHICLE_FIELDS = frozenset({
    "vehicle_type", "model", "capacity", "fuel_type", "status", "rc_status",
    "insurance_status", "puc_status", "fitness_status", "permit_status",
    "current_driver_id",
})

VALID_VEHICLE_STATUSES = frozenset({"AVAILABLE", "IN_TRANSIT", "MAINTENANCE", "INACTIVE", "ACTIVE"})


async def get_all_vehicles(
    db: AsyncSession,
    limit: Optional[int] = None,
    offset: int = 0,
    include_demo: bool = True,
) -> List[Vehicle]:
    stmt = select(Vehicle)
    if not include_demo:
        stmt = stmt.where(Vehicle.is_demo.is_(False))
    stmt = stmt.order_by(Vehicle.created_at.desc()).offset(max(offset, 0))
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_vehicle_by_id(db: AsyncSession, vehicle_id_or_reg: str) -> Optional[Vehicle]:
    """
    Resolve a vehicle by primary key, business id or registration number.

    Registration lookup is case-insensitive: creation uppercases the plate, so
    PATCH /admin/vehicles/mh-04-ab-1234 used to 404 on a vehicle that exists.
    """
    if not vehicle_id_or_reg:
        return None
    reference = vehicle_id_or_reg.strip()
    stmt = select(Vehicle).where(
        or_(
            Vehicle.id == reference,
            Vehicle.vehicle_id == reference,
            func.upper(Vehicle.registration_number) == reference.upper(),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _validate_vehicle_fields(data: Dict[str, Any], *, creating: bool) -> None:
    if "status" in data and data["status"] is not None:
        status = str(data["status"]).upper()
        if status not in VALID_VEHICLE_STATUSES:
            raise AppException(
                message=f"'{data['status']}' is not a recognised vehicle status.",
                code="INVALID_VEHICLE_STATUS",
                status_code=422,
                details={"allowed_statuses": sorted(VALID_VEHICLE_STATUSES)},
            )
    if creating:
        missing = [f for f in ("vehicle_type", "capacity") if not (data.get(f) or "").strip()]
        if missing:
            raise AppException(
                message="Missing vehicle details: " + ", ".join(missing),
                code="VEHICLE_DETAILS_INCOMPLETE",
                status_code=422,
            )


async def create_vehicle(db: AsyncSession, data: Dict[str, Any], actor: str = "system") -> Vehicle:
    _validate_vehicle_fields(data, creating=True)

    reg_number = (data.get("registration_number") or "").strip().upper()
    if not reg_number:
        raise AppException(
            message="Registration number is required.",
            code="INVALID_VEHICLE_DATA",
            status_code=422,
        )

    existing = await get_vehicle_by_id(db, reg_number)
    if existing:
        raise AppException(
            message=f"Vehicle registration number '{reg_number}' already exists.",
            code="VEHICLE_ALREADY_EXISTS",
            status_code=409,
        )

    vehicle = Vehicle(
        id=str(uuid.uuid4()),
        vehicle_id=data.get("vehicle_id") or f"VEH-{uuid.uuid4().hex[:6].upper()}",
        registration_number=reg_number,
        vehicle_type=data["vehicle_type"].strip(),
        model=(data.get("model") or "Not specified").strip(),
        capacity=data["capacity"].strip(),
        fuel_type=(data.get("fuel_type") or "Not specified").strip(),
        status=(data.get("status") or "AVAILABLE").upper(),
        rc_status=data.get("rc_status") or "VALID",
        insurance_status=data.get("insurance_status") or "ACTIVE",
        puc_status=data.get("puc_status") or "VALID",
        fitness_status=data.get("fitness_status") or "VALID",
        permit_status=data.get("permit_status") or "ALL_INDIA_PERMIT",
        current_driver_id=data.get("current_driver_id"),
        is_demo=bool(data.get("is_demo", False)),
    )

    db.add(vehicle)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise AppException(
            message=f"Vehicle registration number '{reg_number}' already exists.",
            code="VEHICLE_ALREADY_EXISTS",
            status_code=409,
        ) from exc

    await create_audit_log(
        db=db,
        actor=actor,
        action="VEHICLE_CREATED",
        entity_type="VEHICLE",
        entity_id=vehicle.registration_number,
        description=f"Created vehicle {vehicle.registration_number} ({vehicle.model})",
        metadata={"registration_number": vehicle.registration_number, "vehicle_id": vehicle.vehicle_id},
        is_demo=vehicle.is_demo,
    )
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def update_vehicle(
    db: AsyncSession,
    vehicle_id_or_reg: str,
    data: Dict[str, Any],
    actor: str = "system",
) -> Vehicle:
    vehicle = await get_vehicle_by_id(db, vehicle_id_or_reg)
    if not vehicle:
        raise AppException(
            message=f"Vehicle '{vehicle_id_or_reg}' not found.",
            code="VEHICLE_NOT_FOUND",
            status_code=404,
        )

    _validate_vehicle_fields(data, creating=False)

    rejected = sorted(set(data) - EDITABLE_VEHICLE_FIELDS - {"registration_number", "vehicle_id"})
    if rejected:
        logger.info(f"Ignoring non-editable vehicle fields: {', '.join(rejected)}")

    applied: Dict[str, Any] = {}
    if (data.get("registration_number") or "").strip():
        applied["registration_number"] = data["registration_number"].strip().upper()

    for field, value in data.items():
        if field in EDITABLE_VEHICLE_FIELDS and value is not None:
            setattr(vehicle, field, value.upper() if field == "status" else value)
            applied[field] = value

    if not applied:
        raise AppException(
            message="No editable vehicle fields were supplied.",
            code="NO_UPDATES",
            status_code=422,
        )

    await create_audit_log(
        db=db,
        actor=actor,
        action="VEHICLE_UPDATED",
        entity_type="VEHICLE",
        entity_id=vehicle.registration_number,
        description=f"Updated vehicle {vehicle.registration_number}",
        metadata=applied,
        is_demo=vehicle.is_demo,
    )
    await db.commit()
    await db.refresh(vehicle)
    return vehicle
