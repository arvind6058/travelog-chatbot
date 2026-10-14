"""Validated request bodies for the admin (logistics console) API."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.shipment_service import ALL_STATUSES


class ShipmentStatusUpdate(BaseModel):
    """Status transitions must be explicit: `status` used to be optional and
    a missing value wrote NULL into a NOT NULL column."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., min_length=2, max_length=32)
    location: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode="after")
    def validate_status(self) -> "ShipmentStatusUpdate":
        normalised = self.status.strip().upper()
        if normalised not in ALL_STATUSES:
            raise ValueError(
                f"'{self.status}' is not a recognised shipment status. "
                f"Allowed: {', '.join(sorted(ALL_STATUSES))}"
            )
        self.status = normalised
        return self


class TrackingEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tracking_id: str = Field(..., min_length=4, max_length=64)
    status: Optional[str] = Field(None, max_length=32)
    location: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=1000)
    event_type: str = Field("LOCATION_UPDATE", max_length=64)

    @model_validator(mode="after")
    def validate_status(self) -> "TrackingEventCreate":
        if self.status:
            normalised = self.status.strip().upper()
            if normalised not in ALL_STATUSES:
                raise ValueError(f"'{self.status}' is not a recognised shipment status.")
            self.status = normalised
        return self


class DriverLocationCreate(BaseModel):
    """Coordinates used to be read from an unvalidated dict, so nonsense such
    as latitude 9999 was persisted and then served to the maps."""

    model_config = ConfigDict(extra="forbid")

    driver_id: str = Field(..., min_length=1, max_length=64)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    accuracy: Optional[float] = Field(None, ge=0)
    location_name: Optional[str] = Field(None, max_length=255)
    vehicle_id: Optional[str] = Field(None, max_length=64)
    shipment_id: Optional[str] = Field(None, max_length=64)
    source: str = Field("gps", max_length=64)


class AssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shipment_id: str = Field(..., min_length=1, max_length=64)
    driver_id: str = Field(..., min_length=1, max_length=64)
    vehicle_id: Optional[str] = Field(None, max_length=64)
    notes: Optional[str] = Field(None, max_length=1000)
