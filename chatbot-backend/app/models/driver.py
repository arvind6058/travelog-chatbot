import uuid
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class Driver(Base, TimestampMixin):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[str] = mapped_column(String(32), nullable=True)
    gender: Mapped[str] = mapped_column(String(16), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(128), nullable=False)
    country: Mapped[str] = mapped_column(String(64), default="India", nullable=False)
    pin: Mapped[str] = mapped_column(String(16), nullable=True)
    kyc_status: Mapped[str] = mapped_column(String(32), default="VERIFIED", nullable=False)
    masked_aadhaar: Mapped[str] = mapped_column(String(32), nullable=True)
    license_number: Mapped[str] = mapped_column(String(64), nullable=True)
    license_status: Mapped[str] = mapped_column(String(32), default="VALID", nullable=False)
    joining_date: Mapped[str] = mapped_column(String(32), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(64), default="FULL_TIME", nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    base_location: Mapped[str] = mapped_column(String(128), nullable=False)
    service_area: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="AVAILABLE", index=True, nullable=False)
    active_vehicle_id: Mapped[str] = mapped_column(String(64), nullable=True)
    current_location: Mapped[str] = mapped_column(String(255), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
