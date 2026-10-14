export type Role = "CUSTOMER" | "LOGISTICS_ADMIN";

export type ShipmentStatus =
  | "REGISTERED"
  | "PICKUP_SCHEDULED"
  | "PICKED_UP"
  | "IN_TRANSIT"
  | "ARRIVED_AT_HUB"
  | "OUT_FOR_DELIVERY"
  | "DELIVERED"
  | "CANCELLED"
  | "FAILED_DELIVERY";

export type DriverStatus =
  | "AVAILABLE"
  | "ON_DELIVERY"
  | "OFFLINE"
  | "SUSPENDED"
  | "INACTIVE";

export type VehicleStatus =
  | "ACTIVE"
  | "IN_TRANSIT"
  | "MAINTENANCE"
  | "DECOMMISSIONED";

export interface ApiStandardError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}
