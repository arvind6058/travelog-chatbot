import uuid
from decimal import Decimal
from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class Shipment(Base, TimestampMixin):
    __tablename__ = "shipments"
    __table_args__ = (
        # Hot paths: fleet/driver views and "my shipments" listings.
        Index("ix_shipments_driver_created", "assigned_driver_id", "created_at"),
        Index("ix_shipments_customer_email", "customer_email"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tracking_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Shipper Details
    shipper_name: Mapped[str] = mapped_column(String(255), nullable=False)
    shipper_phone: Mapped[str] = mapped_column(String(32), nullable=True)
    shipper_address: Mapped[str] = mapped_column(String(255), nullable=True)
    shipper_city: Mapped[str] = mapped_column(String(128), nullable=False)

    # Recipient Details
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(32), nullable=True)
    recipient_address: Mapped[str] = mapped_column(String(255), nullable=True)
    recipient_city: Mapped[str] = mapped_column(String(128), nullable=False)

    # Routing
    origin: Mapped[str] = mapped_column(String(128), nullable=False)
    destination: Mapped[str] = mapped_column(String(128), nullable=False)
    delivery_type: Mapped[str] = mapped_column(String(32), default="STANDARD", nullable=False)

    # Cargo Details
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    package_type: Mapped[str] = mapped_column(String(64), default="Corrugated Box", nullable=False)
    weight_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    dimensions: Mapped[str] = mapped_column(String(64), nullable=True)

    # Schedule & Finance
    # Dates are validated ISO-8601 date strings (YYYY-MM-DD) so lexicographic
    # comparison is meaningful; a Date column is the follow-up migration.
    pickup_date: Mapped[str] = mapped_column(String(32), nullable=True)
    expected_delivery_date: Mapped[str] = mapped_column(String(32), index=True, nullable=True)
    actual_delivery_date: Mapped[str] = mapped_column(String(32), nullable=True)
    # Money must not be stored in binary floating point (18500.10 used to
    # persist as 18500.099999999999 and freight could be set to 0.01).
    cost_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Status & Fleet Assignment
    status: Mapped[str] = mapped_column(String(32), default="REGISTERED", index=True, nullable=False)
    assigned_driver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True
    )
    assigned_vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True
    )
    current_location: Mapped[str] = mapped_column(String(255), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)

