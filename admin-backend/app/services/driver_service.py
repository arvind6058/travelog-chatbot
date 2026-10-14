import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import logger
from app.models.driver import Driver
from app.models.driver_location import DriverLocation
from app.services.audit_service import create_audit_log

# Fields an operator may change through the API. Mass assignment previously
# allowed rewriting the primary key, created_at and the is_demo audit flag.
EDITABLE_DRIVER_FIELDS = frozenset({
    "full_name", "phone", "email", "date_of_birth", "gender", "address", "city",
    "state", "country", "pin", "kyc_status", "masked_aadhaar", "license_number",
    "license_status", "joining_date", "employment_type", "experience_years",
    "base_location", "service_area", "status", "active_vehicle_id",
})

VALID_DRIVER_STATUSES = frozenset({"AVAILABLE", "ON_DELIVERY", "INACTIVE", "SUSPENDED"})


async def get_all_drivers(
    db: AsyncSession,
    limit: Optional[int] = None,
    offset: int = 0,
    include_demo: bool = True,
) -> List[Driver]:
    stmt = select(Driver)
    if not include_demo:
        stmt = stmt.where(Driver.is_demo.is_(False))
    stmt = stmt.order_by(Driver.created_at.desc()).offset(max(offset, 0))
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_driver_by_id(db: AsyncSession, driver_id_or_uuid: str) -> Optional[Driver]:
    stmt = select(Driver).where(
        or_(Driver.id == driver_id_or_uuid, Driver.driver_id == driver_id_or_uuid)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_eligible_drivers(db: AsyncSession) -> List[Driver]:
    """Drivers who are available, verified, and hold a valid license."""
    stmt = select(Driver).where(
        Driver.status.in_(["AVAILABLE", "ACTIVE"]),
        Driver.license_status == "VALID",
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _validate_driver_fields(data: Dict[str, Any], *, creating: bool) -> None:
    if "status" in data and data["status"] is not None:
        status = str(data["status"]).upper()
        if status not in VALID_DRIVER_STATUSES:
            raise AppException(
                message=f"'{data['status']}' is not a recognised driver status.",
                code="INVALID_DRIVER_STATUS",
                status_code=422,
                details={"allowed_statuses": sorted(VALID_DRIVER_STATUSES)},
            )
    if creating and not (data.get("full_name") or "").strip():
        raise AppException(
            message="full_name is required to create a driver.",
            code="DRIVER_DETAILS_INCOMPLETE",
            status_code=422,
        )


async def create_driver(db: AsyncSession, data: Dict[str, Any], actor: str = "system") -> Driver:
    _validate_driver_fields(data, creating=True)

    driver_id_input = data.get("driver_id") or f"DRV-{uuid.uuid4().hex[:6].upper()}"
    existing = await get_driver_by_id(db, driver_id_input)
    if existing:
        raise AppException(
            message=f"Driver ID '{driver_id_input}' already exists.",
            code="DRIVER_ALREADY_EXISTS",
            status_code=409,
        )

    driver = Driver(
        id=str(uuid.uuid4()),
        driver_id=driver_id_input,
        full_name=data["full_name"].strip(),
        phone=data.get("phone") or "",
        email=data.get("email"),
        date_of_birth=data.get("date_of_birth"),
        gender=data.get("gender"),
        address=data.get("address"),
        city=data.get("city") or "",
        state=data.get("state") or "",
        country=data.get("country") or "India",
        pin=data.get("pin"),
        kyc_status=data.get("kyc_status") or "PENDING",
        masked_aadhaar=data.get("masked_aadhaar"),
        license_number=data.get("license_number"),
        license_status=data.get("license_status") or "VALID",
        joining_date=data.get("joining_date"),
        employment_type=data.get("employment_type") or "FULL_TIME",
        experience_years=data.get("experience_years") or 0,
        base_location=data.get("base_location") or "",
        service_area=data.get("service_area") or "",
        status=(data.get("status") or "AVAILABLE").upper(),
        active_vehicle_id=data.get("active_vehicle_id"),
        current_location=data.get("current_location"),
        is_demo=bool(data.get("is_demo", False)),
    )

    db.add(driver)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise AppException(
            message=f"Driver ID '{driver_id_input}' already exists.",
            code="DRIVER_ALREADY_EXISTS",
            status_code=409,
        ) from exc

    await create_audit_log(
        db=db,
        actor=actor,
        action="DRIVER_CREATED",
        entity_type="DRIVER",
        entity_id=driver.driver_id,
        description=f"Created driver {driver.full_name} ({driver.driver_id})",
        metadata={"driver_id": driver.driver_id, "full_name": driver.full_name},
        is_demo=driver.is_demo,
    )
    await db.commit()
    await db.refresh(driver)
    return driver


async def update_driver(
    db: AsyncSession,
    driver_id_or_uuid: str,
    data: Dict[str, Any],
    actor: str = "system",
) -> Driver:
    driver = await get_driver_by_id(db, driver_id_or_uuid)
    if not driver:
        raise AppException(
            message=f"Driver '{driver_id_or_uuid}' not found.",
            code="DRIVER_NOT_FOUND",
            status_code=404,
        )

    _validate_driver_fields(data, creating=False)

    rejected = sorted(set(data) - EDITABLE_DRIVER_FIELDS - {"driver_id"})
    if rejected:
        logger.info(f"Ignoring non-editable driver fields: {', '.join(rejected)}")

    applied: Dict[str, Any] = {}
    for field, value in data.items():
        if field in EDITABLE_DRIVER_FIELDS and value is not None:
            setattr(driver, field, value)
            applied[field] = value

    if not applied:
        raise AppException(
            message="No editable driver fields were supplied.",
            code="NO_UPDATES",
            status_code=422,
        )

    await create_audit_log(
        db=db,
        actor=actor,
        action="DRIVER_UPDATED",
        entity_type="DRIVER",
        entity_id=driver.driver_id,
        description=f"Updated driver {driver.driver_id}",
        metadata=applied,
        is_demo=driver.is_demo,
    )
    await db.commit()
    await db.refresh(driver)
    return driver


def validate_coordinates(
    latitude: Optional[float],
    longitude: Optional[float],
    accuracy: Optional[float] = None,
) -> None:
    """Reject physically impossible telemetry before it reaches the maps."""
    if latitude is None or longitude is None:
        raise AppException(
            message="latitude and longitude are required.",
            code="INVALID_COORDINATES",
            status_code=422,
        )
    if not (-90.0 <= float(latitude) <= 90.0):
        raise AppException(
            message="latitude must be between -90 and 90.",
            code="INVALID_COORDINATES",
            status_code=422,
        )
    if not (-180.0 <= float(longitude) <= 180.0):
        raise AppException(
            message="longitude must be between -180 and 180.",
            code="INVALID_COORDINATES",
            status_code=422,
        )
    if accuracy is not None and float(accuracy) < 0:
        raise AppException(
            message="accuracy cannot be negative.",
            code="INVALID_COORDINATES",
            status_code=422,
        )


async def record_driver_location(
    db: AsyncSession,
    driver_id_or_code: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    accuracy: Optional[float] = None,
    location_name: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    shipment_id: Optional[str] = None,
    source: str = "gps",
    mode: Optional[str] = None,
    is_mock: Optional[bool] = None,
    actor: str = "fleet_telemetry",
) -> DriverLocation:
    driver = await get_driver_by_id(db, driver_id_or_code)
    if not driver:
        raise AppException(
            message=f"Driver '{driver_id_or_code}' not found.",
            code="DRIVER_NOT_FOUND",
            status_code=404,
        )

    validate_coordinates(latitude, longitude, accuracy)

    loc_name = location_name or driver.current_location or "Unknown Location"

    # mode/is_mock describe provenance and are derived server-side: a caller
    # used to be able to label their own writes as demo data (or hide demo data
    # as live) and pre-tag audit rows.
    derived_mock = bool(driver.is_demo) if is_mock is None else bool(is_mock)
    derived_mode = mode or ("demo" if derived_mock else "live")

    loc_entry = DriverLocation(
        id=str(uuid.uuid4()),
        driver_id=driver.id,
        vehicle_id=vehicle_id or driver.active_vehicle_id,
        shipment_id=shipment_id,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        location_name=loc_name,
        source=source,
        mode=derived_mode,
        is_mock=derived_mock,
        recorded_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db.add(loc_entry)

    await create_audit_log(
        db=db,
        actor=actor,
        action="DRIVER_LOCATION_UPDATED",
        entity_type="DRIVER",
        entity_id=driver.driver_id,
        description=f"Recorded driver location for {driver.driver_id}: {loc_name}",
        metadata={"latitude": latitude, "longitude": longitude, "location": loc_name},
        is_demo=derived_mock,
    )
    await db.commit()
    await db.refresh(loc_entry)

    try:
        from app.realtime.manager import manager as realtime_manager

        event_payload = {
            "event": "driver.location_changed",
            "driver_id": driver.driver_id,
            "location": loc_name,
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy,
            "mode": derived_mode,
            "timestamp": loc_entry.recorded_at.isoformat(),
        }
        await realtime_manager.broadcast_to_channel(f"drivers:{driver.driver_id}", event_payload)
        await realtime_manager.broadcast_to_channel("drivers:all", event_payload)
    except Exception as exc:  # pragma: no cover - telemetry is not critical
        logger.warning(f"Realtime location broadcast skipped: {exc}")

    return loc_entry
