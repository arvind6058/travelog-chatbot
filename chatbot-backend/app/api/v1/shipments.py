from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_customer, get_optional_customer
from app.db.session import get_db_session
from app.realtime.manager import manager as realtime_manager
from app.schemas.shipment import ShipmentCreateSchema, ShipmentTrackingPublic
from app.services import shipment_service, tracking_service

router = APIRouter(prefix="/shipments", tags=["Shipments"])


def _shipment_summary(s: Any) -> Dict[str, Any]:
    """Explicit projection: never reflect raw ORM columns to the client."""
    return {
        "id": s.id,
        "tracking_id": s.tracking_id,
        "customer_name": s.customer_name,
        "customer_email": s.customer_email,
        "shipper_name": s.shipper_name,
        "recipient_name": s.recipient_name,
        "package_name": s.package_name,
        "delivery_type": s.delivery_type,
        "origin": s.origin,
        "destination": s.destination,
        "weight_kg": float(s.weight_kg) if s.weight_kg is not None else None,
        "cost_inr": float(s.cost_inr) if s.cost_inr is not None else None,
        "pickup_date": s.pickup_date,
        "expected_delivery_date": s.expected_delivery_date,
        "status": s.status,
        "current_location": s.current_location,
        "is_demo": bool(s.is_demo),
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _shipment_public(s: Any) -> Dict[str, Any]:
    """
    Anonymous tracking view.

    Public tracking stays available (customers track by id without signing in),
    but names, emails, addresses and freight cost are never disclosed.
    """
    return {
        "tracking_id": s.tracking_id,
        "status": s.status,
        "origin": s.origin,
        "destination": s.destination,
        "current_location": s.current_location,
        "pickup_date": s.pickup_date,
        "expected_delivery_date": s.expected_delivery_date,
        "actual_delivery_date": s.actual_delivery_date,
        "is_demo": bool(s.is_demo),
    }


@router.post("", summary="Register a new shipment")
@router.post("/", summary="Register a new shipment")
async def register_shipment(
    payload: ShipmentCreateSchema,
    current_customer: Dict[str, Any] = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Register a shipment for the signed-in customer.

    Authentication is required and the owning email comes from the session, so
    freight can no longer be created anonymously or attributed to someone else.
    """
    shipment_dict = payload.model_dump()
    shipment_dict["customer_email"] = current_customer.get("email")
    shipment_dict["customer_name"] = current_customer.get("name") or current_customer.get("email")
    # A customer may never set fleet assignment or demo flags directly.
    shipment_dict.pop("assigned_driver_id", None)
    shipment_dict.pop("assigned_vehicle_id", None)
    shipment_dict.pop("customer_id", None)
    shipment_dict["is_demo"] = False

    shipment = await shipment_service.create_shipment(
        db, shipment_dict, actor=str(current_customer.get("email"))
    )

    try:
        await realtime_manager.broadcast_to_channel(
            f"tracking:{shipment.tracking_id}",
            {
                "event": "shipment.registered",
                "tracking_id": shipment.tracking_id,
                "status": shipment.status,
                "origin": shipment.origin,
                "destination": shipment.destination,
            },
        )
    except Exception:
        pass

    return {
        "success": True,
        "message": "Shipment registered successfully.",
        "shipment": _shipment_summary(shipment),
    }


@router.get("", summary="List the signed-in customer's shipments")
@router.get("/", summary="List the signed-in customer's shipments")
async def list_shipments(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_customer: Dict[str, Any] = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Only the caller's own shipments.

    Previously this endpoint accepted `?email=` (and returned every customer's
    shipments when it was omitted) without ever reading the session.
    """
    email = str(current_customer.get("email"))
    shipments = await shipment_service.get_all_shipments(
        db, limit=limit, offset=offset, customer_email=email
    )
    total = await shipment_service.count_shipments(db, customer_email=email)
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "shipments": [_shipment_summary(s) for s in shipments],
    }


@router.get("/{tracking_id_or_id}", summary="Track a shipment by tracking id")
async def get_shipment_details(
    tracking_id_or_id: str,
    current_customer: Optional[Dict[str, Any]] = Depends(get_optional_customer),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Public tracking with a sanitized payload; owners get the full record.
    """
    shipment = await shipment_service.get_shipment_by_id_or_tracking(db, tracking_id_or_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")

    is_owner = bool(current_customer) and (
        (shipment.customer_email or "").lower() == str(current_customer.get("email", "")).lower()
    )

    if not is_owner:
        return {
            "success": True,
            "shipment": _shipment_public(shipment),
            "events": [],
            "access": "public",
        }

    tracking_full = await tracking_service.get_shipment_tracking_full(db, shipment.tracking_id)
    return {
        "success": True,
        "shipment": _shipment_summary(shipment),
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "status": e.status,
                "location": e.location,
                "message": e.message,
                "mode": e.mode,
                "is_mock": bool(e.is_mock),
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in tracking_full.get("events", [])
        ],
        "access": "owner",
    }


# Logistics aliases for requirements (/api/v1/logistics/tracking/{tracking_id} & /history)
logistics_router = APIRouter(prefix="/logistics", tags=["Logistics"])

@logistics_router.get("/tracking/{tracking_id}", summary="Public tracking for customer")
async def logistics_tracking(
    tracking_id: str,
    current_customer: Optional[Dict[str, Any]] = Depends(get_optional_customer),
    db: AsyncSession = Depends(get_db_session),
):
    return await get_shipment_details(tracking_id_or_id=tracking_id, current_customer=current_customer, db=db)

@logistics_router.get("/shipments/{tracking_id}/history", summary="Shipment event history for customer")
async def logistics_shipment_history(
    tracking_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    shipment = await shipment_service.get_shipment_by_id_or_tracking(db, tracking_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")
    events = await tracking_service.get_shipment_events(db, tracking_id)
    return {
        "success": True,
        "tracking_id": shipment.tracking_id,
        "status": shipment.status,
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "status": e.status,
                "location": e.location,
                "message": e.message,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ]
    }

