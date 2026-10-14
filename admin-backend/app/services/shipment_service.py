import secrets
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import logger
from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.services.audit_service import create_audit_log

VALID_TRANSITIONS = {
    "REGISTERED": ["PICKUP_SCHEDULED", "PICKED_UP", "CANCELLED"],
    "PICKUP_SCHEDULED": ["PICKED_UP", "CANCELLED"],
    "PICKED_UP": ["IN_TRANSIT", "ARRIVED_AT_HUB", "CANCELLED"],
    "IN_TRANSIT": ["ARRIVED_AT_HUB", "OUT_FOR_DELIVERY", "DELAYED", "CANCELLED"],
    "ARRIVED_AT_HUB": ["IN_TRANSIT", "OUT_FOR_DELIVERY", "CANCELLED"],
    "OUT_FOR_DELIVERY": ["DELIVERED", "FAILED_DELIVERY", "IN_TRANSIT", "CANCELLED"],
    "DELAYED": ["IN_TRANSIT", "OUT_FOR_DELIVERY", "CANCELLED"],
    "FAILED_DELIVERY": ["OUT_FOR_DELIVERY", "CANCELLED"],
    "DELIVERED": [],
    "CANCELLED": [],
}

# Statuses a shipment may be moved to from anywhere (operational overrides).
GLOBAL_TARGET_STATUSES = {"CANCELLED", "DELAYED"}

ALL_STATUSES = frozenset(VALID_TRANSITIONS)

# Fields the caller must supply; the service never invents freight details.
REQUIRED_CREATE_FIELDS = ("origin", "destination", "weight_kg")

_ANONYMOUS_ACTOR = "anonymous"


def generate_tracking_id() -> str:
    """
    Generate an unguessable tracking id.

    Previously an 8-char `random.choices` value (Mersenne Twister, not
    cryptographically random) with a check-then-insert uniqueness test, which
    two concurrent requests could both pass.
    """
    return f"TLX-{secrets.token_hex(4).upper()}"


def _pick(data: Dict[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        value = data.get(key)
        if value is not None and value != "":
            return value
    return None


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_iso_date(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Reads
# --------------------------------------------------------------------------- #
async def get_all_shipments(
    db: AsyncSession,
    limit: Optional[int] = None,
    offset: int = 0,
    customer_email: Optional[str] = None,
    include_demo: bool = True,
) -> List[Shipment]:
    stmt = select(Shipment)
    if customer_email:
        stmt = stmt.where(func.lower(Shipment.customer_email) == customer_email.lower())
    if not include_demo:
        stmt = stmt.where(Shipment.is_demo.is_(False))
    stmt = stmt.order_by(Shipment.created_at.desc()).offset(max(offset, 0))
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_shipments(
    db: AsyncSession,
    customer_email: Optional[str] = None,
    include_demo: bool = True,
) -> int:
    stmt = select(func.count(Shipment.id))
    if customer_email:
        stmt = stmt.where(func.lower(Shipment.customer_email) == customer_email.lower())
    if not include_demo:
        stmt = stmt.where(Shipment.is_demo.is_(False))
    return int((await db.execute(stmt)).scalar_one())


async def get_shipment_by_id_or_tracking(db: AsyncSession, tracking_id_or_id: str) -> Optional[Shipment]:
    stmt = select(Shipment).where(
        or_(
            Shipment.id == tracking_id_or_id,
            Shipment.tracking_id == tracking_id_or_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_delayed_shipments(
    db: AsyncSession,
    limit: Optional[int] = None,
    offset: int = 0,
    include_demo: bool = True,
) -> List[Shipment]:
    """
    Shipments that are late or flagged delayed.

    The past-due test now runs in SQL against ISO-formatted dates instead of a
    Python string comparison against the server's local clock.
    """
    today = date.today().isoformat()
    stmt = select(Shipment).where(
        Shipment.status.in_(["DELAYED", "IN_TRANSIT", "OUT_FOR_DELIVERY", "ARRIVED_AT_HUB", "PICKED_UP"]),
        or_(
            Shipment.status == "DELAYED",
            Shipment.expected_delivery_date < today,
        ),
    )
    if not include_demo:
        stmt = stmt.where(Shipment.is_demo.is_(False))
    stmt = stmt.order_by(Shipment.expected_delivery_date.asc()).offset(max(offset, 0))
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_delivered_shipments(
    db: AsyncSession,
    limit: Optional[int] = None,
    offset: int = 0,
    include_demo: bool = True,
) -> List[Shipment]:
    stmt = select(Shipment).where(Shipment.status == "DELIVERED")
    if not include_demo:
        stmt = stmt.where(Shipment.is_demo.is_(False))
    # Order by the real delivery date when present, else last update.
    stmt = stmt.order_by(Shipment.actual_delivery_date.desc().nulls_last()).offset(max(offset, 0))
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


# --------------------------------------------------------------------------- #
# Writes
# --------------------------------------------------------------------------- #
def _estimate_freight(weight_kg: float, delivery_type: str) -> Decimal:
    rate = Decimal("350.00")
    lowered = (delivery_type or "").lower()
    if "express" in lowered or "priority" in lowered:
        rate = Decimal("650.00")
    elif "same day" in lowered:
        rate = Decimal("1200.00")
    return (rate + (Decimal(str(weight_kg)) * Decimal("85.00"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


async def create_shipment(
    db: AsyncSession,
    data: Dict[str, Any],
    actor: Optional[str] = None,
) -> Shipment:
    """
    Register a shipment.

    Every material detail must come from the caller: the previous version
    silently substituted invented values such as origin "Mumbai Hub",
    destination "Delhi Hub" and `client@travelogix.internal` whenever a field
    was missing, which produced freight records nobody asked for.
    """
    # Support both snake_case and camelCase field keys
    origin = _pick(data, "origin", "originCity", "origin_city")
    destination = _pick(data, "destination", "destinationCity", "destination_city")
    weight_raw = _pick(data, "weight_kg", "weightKg", "weight")
    customer_email = _pick(data, "customer_email", "customerEmail")

    missing = [
        name
        for name, value in (("origin", origin), ("destination", destination), ("weight_kg", weight_raw))
        if value in (None, "")
    ]
    if missing:
        raise AppException(
            message="Shipment details are incomplete: " + ", ".join(missing) + " required.",
            code="SHIPMENT_DETAILS_INCOMPLETE",
            status_code=422,
            details={"missing_fields": missing},
        )

    if not customer_email:
        raise AppException(
            message="A signed-in customer is required to register a shipment.",
            code="CUSTOMER_IDENTITY_REQUIRED",
            status_code=401,
        )

    weight_kg = _to_float(weight_raw)
    if weight_kg is None or weight_kg <= 0:
        raise AppException(
            message="Weight must be a positive number of kilograms.",
            code="INVALID_WEIGHT",
            status_code=422,
        )

    customer_name = _pick(data, "customer_name", "customerName", "customerEntity") or customer_email
    delivery_type = _pick(data, "delivery_type", "deliveryType") or "STANDARD"

    cost_inr = _to_decimal(_pick(data, "cost_inr", "estimatedCost"))
    if cost_inr is None or cost_inr <= 0:
        # A *derived* estimate, never a made-up authoritative price.
        cost_inr = _estimate_freight(weight_kg, delivery_type)

    pickup_date = _to_iso_date(_pick(data, "pickup_date", "pickupDate")) or date.today().isoformat()
    expected_delivery_date = _to_iso_date(
        _pick(data, "expected_delivery_date", "expectedDeliveryDate")
    ) or pickup_date

    if expected_delivery_date < pickup_date:
        raise AppException(
            message="Expected delivery date cannot be before the pickup date.",
            code="INVALID_DELIVERY_DATES",
            status_code=422,
        )

    is_demo = bool(data.get("is_demo", False))

    shipment = Shipment(
        id=str(uuid.uuid4()),
        customer_id=_pick(data, "customer_id"),
        customer_name=customer_name,
        customer_email=customer_email,
        shipper_name=_pick(data, "shipper_name", "shipperName") or customer_name,
        shipper_phone=_pick(data, "shipper_phone", "shipperPhone"),
        shipper_address=_pick(data, "shipper_address", "shipperAddress") or f"{origin} Logistics Center",
        shipper_city=origin,
        recipient_name=_pick(data, "recipient_name", "recipientName") or customer_name,
        recipient_phone=_pick(data, "recipient_phone", "recipientPhone"),
        recipient_address=_pick(data, "recipient_address", "recipientAddress") or f"{destination} Receiving Hub",
        recipient_city=destination,
        origin=origin,
        destination=destination,
        delivery_type=delivery_type,
        package_name=_pick(data, "package_name", "cargoDescription", "package") or "General Freight",
        package_type=_pick(data, "package_type", "packageType") or "Corrugated Box",
        weight_kg=weight_kg,
        dimensions=_pick(data, "dimensions") or "Not specified",
        pickup_date=pickup_date,
        expected_delivery_date=expected_delivery_date,
        cost_inr=cost_inr,
        status="REGISTERED",
        current_location=origin,
        is_demo=is_demo,
    )

    # Let the database arbitrate uniqueness instead of check-then-insert.
    for attempt in range(5):
        shipment.tracking_id = _pick(data, "tracking_id") or generate_tracking_id()
        db.add(shipment)
        try:
            await db.flush()
            break
        except IntegrityError:
            await db.rollback()
            if _pick(data, "tracking_id"):
                raise AppException(
                    message="That tracking id is already in use.",
                    code="TRACKING_ID_CONFLICT",
                    status_code=409,
                )
            logger.warning(f"Tracking id collision on attempt {attempt + 1}; regenerating.")
    else:
        raise AppException(
            message="Could not allocate a unique tracking id. Please retry.",
            code="TRACKING_ID_ALLOCATION_FAILED",
            status_code=503,
        )

    db.add(
        ShipmentEvent(
            id=str(uuid.uuid4()),
            shipment_id=shipment.id,
            tracking_id=shipment.tracking_id,
            event_type="REGISTERED",
            status="REGISTERED",
            location=origin,
            message=f"Shipment registered at {origin}. Pending pickup scheduling.",
            source="travelogix_ops",
            mode="demo" if is_demo else "live",
            is_mock=is_demo,
            timestamp=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
    )

    await create_audit_log(
        db=db,
        actor=actor or customer_email,
        action="SHIPMENT_CREATED",
        entity_type="SHIPMENT",
        entity_id=shipment.tracking_id,
        description=f"Registered shipment {shipment.tracking_id} from {origin} to {destination}",
        metadata={"tracking_id": shipment.tracking_id, "cost_inr": str(shipment.cost_inr)},
        is_demo=is_demo,
    )

    await db.commit()
    await db.refresh(shipment)
    return shipment


async def update_shipment_status(
    db: AsyncSession,
    tracking_id_or_id: str,
    new_status: str,
    location: Optional[str] = None,
    message: Optional[str] = None,
    actor: str = "system",
    mode: Optional[str] = None,
    is_mock: Optional[bool] = None,
) -> Shipment:
    """
    Move a shipment to a new status, enforcing the state machine.

    The previous transition check was dead code (`if ...: pass`), so any string
    was accepted and `null` wrote NULL into a NOT NULL column.
    """
    shipment = await get_shipment_by_id_or_tracking(db, tracking_id_or_id)
    if not shipment:
        raise AppException(
            message=f"Shipment '{tracking_id_or_id}' not found.",
            code="SHIPMENT_NOT_FOUND",
            status_code=404,
        )

    if not new_status or not isinstance(new_status, str):
        raise AppException(
            message="A target status is required.",
            code="INVALID_STATUS",
            status_code=422,
        )

    new_status = new_status.strip().upper()
    if new_status not in ALL_STATUSES:
        raise AppException(
            message=f"'{new_status}' is not a recognised shipment status.",
            code="INVALID_STATUS",
            status_code=422,
            details={"allowed_statuses": sorted(ALL_STATUSES)},
        )

    old_status = shipment.status
    if new_status != old_status:
        allowed_next = VALID_TRANSITIONS.get(old_status, [])
        if new_status not in allowed_next and new_status not in GLOBAL_TARGET_STATUSES:
            raise AppException(
                message=f"Cannot move a shipment from {old_status} to {new_status}.",
                code="INVALID_STATUS_TRANSITION",
                status_code=409,
                details={"from": old_status, "to": new_status, "allowed": allowed_next},
            )

    shipment.status = new_status
    if location:
        shipment.current_location = location
    if new_status == "DELIVERED":
        shipment.actual_delivery_date = datetime.now(timezone.utc).date().isoformat()

    evt_location = location or shipment.current_location or shipment.origin
    derived_mode = mode or ("demo" if shipment.is_demo else "live")
    derived_mock = shipment.is_demo if is_mock is None else is_mock

    db.add(
        ShipmentEvent(
            id=str(uuid.uuid4()),
            shipment_id=shipment.id,
            tracking_id=shipment.tracking_id,
            event_type=f"STATUS_{new_status}",
            status=new_status,
            location=evt_location,
            message=message or f"Consignment status updated to {new_status} at {evt_location}",
            source="travelogix_ops",
            mode=derived_mode,
            is_mock=derived_mock,
            timestamp=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
    )

    await create_audit_log(
        db=db,
        actor=actor,
        action="SHIPMENT_STATUS_UPDATED",
        entity_type="SHIPMENT",
        entity_id=shipment.tracking_id,
        description=f"Changed status of {shipment.tracking_id} from {old_status} to {new_status}",
        metadata={"old_status": old_status, "new_status": new_status, "location": evt_location},
        is_demo=derived_mock,
    )

    # Free the driver/vehicle and close the active assignment.
    if new_status in ("DELIVERED", "CANCELLED"):
        from app.services.assignment_service import close_active_assignment

        await close_active_assignment(db, shipment)

    await db.commit()
    await db.refresh(shipment)
    return shipment
