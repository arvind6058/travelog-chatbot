import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    registration_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(64), nullable=False)  # Mini Truck, Van, Flatbed, Heavy Container
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    capacity: Mapped[str] = mapped_column(String(64), nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(32), default="Diesel", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True, nullable=False)  # ACTIVE, IN_TRANSIT, MAINTENANCE
    rc_status: Mapped[str] = mapped_column(String(32), default="VALID", nullable=False)
    insurance_status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    puc_status: Mapped[str] = mapped_column(String(32), default="VALID", nullable=False)
    fitness_status: Mapped[str] = mapped_column(String(32), default="VALID", nullable=False)
    permit_status: Mapped[str] = mapped_column(String(64), default="ALL_INDIA_PERMIT", nullable=False)
    current_driver_id: Mapped[str] = mapped_column(String(64), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
