from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, condecimal, model_validator

Money = condecimal(gt=0, max_digits=12, decimal_places=2)


class ShipmentCreateSchema(BaseModel):
    """
    Payload for registering a shipment.

    `customer_email` / `customer_name` are accepted for backwards compatibility
    but ignored: the owning identity always comes from the authenticated session.
    Unknown fields are rejected so fleet-assignment and demo flags cannot be
    injected through the body.
    """

    model_config = ConfigDict(extra="forbid")

    customer_email: Optional[EmailStr] = Field(None, description="Ignored: taken from the session")
    customer_name: Optional[str] = Field(None, max_length=255, description="Ignored: taken from the session")

    shipper_name: str = Field(..., min_length=1, max_length=255)
    recipient_name: str = Field(..., min_length=1, max_length=255)
    package_name: str = Field(..., min_length=1, max_length=255)
    delivery_type: str = Field(..., min_length=1, max_length=32)
    origin: str = Field(..., min_length=1, max_length=128)
    destination: str = Field(..., min_length=1, max_length=128)
    weight_kg: float = Field(..., gt=0, le=100000, description="Weight in kg, greater than 0")
    cost_inr: Optional[Money] = Field(None, description="Estimated cost in INR; server estimates when omitted")

    # Real date validation: these used to be free-form strings compared
    # lexicographically, so "01/02/2026" and "2026-1-5" were both accepted.
    pickup_date: date = Field(..., description="Pickup date (YYYY-MM-DD)")
    expected_delivery_date: date = Field(..., description="Expected delivery date (YYYY-MM-DD)")

    shipper_phone: Optional[str] = Field(None, max_length=32)
    recipient_phone: Optional[str] = Field(None, max_length=32)
    shipper_address: Optional[str] = Field(None, max_length=255)
    recipient_address: Optional[str] = Field(None, max_length=255)
    package_type: Optional[str] = Field(None, max_length=64)
    dimensions: Optional[str] = Field(None, max_length=64)

    @model_validator(mode="after")
    def validate_dates(self) -> "ShipmentCreateSchema":
        if self.expected_delivery_date < self.pickup_date:
            raise ValueError("Expected Delivery Date cannot be before Pickup Date.")
        return self


class ShipmentTrackingPublic(BaseModel):
    """Anonymous tracking view: no customer, contact or pricing details."""

    tracking_id: str
    status: str
    origin: str
    destination: str
    current_location: Optional[str] = None
    pickup_date: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    actual_delivery_date: Optional[str] = None
    is_demo: bool = False
    found: bool = True
