import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="CUSTOMER", index=True, nullable=False)  # "CUSTOMER" or "LOGISTICS_ADMIN"
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
