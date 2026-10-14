from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.driver import Driver
from app.models.vehicle import Vehicle


class CourierProvider:
    """
    Courier logistics provider adapter connecting directly to PostgreSQL backend database.
    Ensures single source of truth between Customer and Admin.
    """

    def __init__(self, mode: str = "live"):
        self.mode = mode

    async def get_shipment_details(self, tracking_id: str, db: AsyncSession) -> Dict[str, Any]:
        stmt = select(Shipment).where(Shipment.tracking_id == tracking_id)
        res = await db.execute(stmt)
        shipment = res.scalar_one_or_none()

        if not shipment:
            return {
                "found": False,
                "tracking_id": tracking_id,
                "message": f"Shipment with tracking ID '{tracking_id}' was not found in Travelogix Logistics Core Database.",
                "provenance": {
                    "source": "travelogix_database",
                    "mode": "unavailable",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "is_mock": False
                }
            }

        # Fetch events
        stmt_e = select(ShipmentEvent).where(ShipmentEvent.shipment_id == shipment.id).order_by(ShipmentEvent.timestamp.asc())
        events_res = await db.execute(stmt_e)
        events = list(events_res.scalars().all())

        # Fetch assigned driver & vehicle if any
        driver_info = None
        if shipment.assigned_driver_id:
            d_res = await db.execute(select(Driver).where(Driver.id == shipment.assigned_driver_id))
            drv = d_res.scalar_one_or_none()
            if drv:
                driver_info = {
                    "driver_id": drv.driver_id,
                    "name": drv.full_name,
                    "phone": drv.phone,
                    "current_location": drv.current_location
                }

        vehicle_info = None
        if shipment.assigned_vehicle_id:
            v_res = await db.execute(select(Vehicle).where(Vehicle.id == shipment.assigned_vehicle_id))
            veh = v_res.scalar_one_or_none()
            if veh:
                vehicle_info = {
                    "vehicle_id": veh.vehicle_id,
                    "registration_number": veh.registration_number,
                    "model": veh.model,
                    "vehicle_type": veh.vehicle_type
                }

        return {
            "found": True,
            "tracking_id": shipment.tracking_id,
            "status": shipment.status,
            "origin": shipment.origin,
            "destination": shipment.destination,
            "verified_location": shipment.current_location,
            "shipper": shipment.shipper_name,
            "recipient": shipment.recipient_name,
            "package_name": shipment.package_name,
            "weight_kg": shipment.weight_kg,
            "pickup_date": shipment.pickup_date,
            "expected_delivery_date": shipment.expected_delivery_date,
            "cost_inr": shipment.cost_inr,
            "driver": driver_info,
            "vehicle": vehicle_info,
            "history": [
                {
                    "event_type": e.event_type,
                    "status": e.status,
                    "location": e.location,
                    "message": e.message,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None
                }
                for e in events
            ],
            "provenance": {
                "source": "travelogix_postgresql_db",
                "mode": "demo" if shipment.is_demo else "live",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "is_mock": shipment.is_demo
            }
        }
