"use client";

import React from "react";
import { Truck, MapPin, User, Clock, AlertCircle, ShieldCheck } from "lucide-react";
import { TrackingTimeline, TimelineItem } from "./TrackingTimeline";

interface DriverTrackingPanelProps {
  driver: any | null;
  isLoading?: boolean;
  error?: string | null;
}

export const DriverTrackingPanel: React.FC<DriverTrackingPanelProps> = ({
  driver,
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-full min-h-[440px] flex flex-col items-center justify-center text-slate-500">
        <Truck className="w-8 h-8 animate-bounce text-indigo-400 mb-2" />
        <span className="text-xs font-semibold">Loading driver tracking telemetry...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-full min-h-[440px] flex flex-col items-center justify-center text-center p-6">
        <AlertCircle className="w-10 h-10 text-rose-500 mb-2" />
        <h4 className="text-sm font-bold text-white mb-1">Driver Not Found</h4>
        <p className="text-xs text-rose-300 max-w-xs">{error}</p>
      </div>
    );
  }

  if (!driver) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-full min-h-[440px] flex flex-col items-center justify-center text-center text-slate-500">
        <Truck className="w-10 h-10 text-slate-700 mb-2" />
        <h4 className="text-sm font-bold text-slate-300 mb-1">No Driver Selected</h4>
        <p className="text-xs text-slate-500 max-w-xs">
          Select a driver from the dropdown above to inspect vehicle, location and location history.
        </p>
      </div>
    );
  }

  // Format driver location history items for timeline
  const historyItems: TimelineItem[] = (driver.location_history || []).map((loc: any, idx: number) => ({
    id: loc.id || `loc-${idx}`,
    title: loc.location_name || driver.current_location || "LOCATION_UPDATED",
    description: loc.source ? `Source: ${loc.source}` : undefined,
    location: loc.location_name,
    latitude: loc.latitude,
    longitude: loc.longitude,
    timestamp: loc.recorded_at || loc.created_at,
    isLatest: idx === 0,
  }));

  const isMock = driver.is_mock ?? true;
  const hasCoords = typeof driver.latitude === "number" && typeof driver.longitude === "number";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 md:p-6 space-y-6 h-full overflow-y-auto max-h-[600px] shadow-xl">
      {/* Header Info */}
      <div className="border-b border-slate-800 pb-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">{driver.full_name}</h3>
            <span className="text-xs font-mono text-indigo-400 font-semibold">{driver.driver_id}</span>
          </div>

          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
            isMock
              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
              : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
          }`}>
            {isMock ? "DEMO DATA" : "LIVE"}
          </span>
        </div>

        {/* Status + Location Cards */}
        <div className="grid grid-cols-2 gap-2.5 text-xs">
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="text-slate-500 block text-[10px] font-semibold uppercase tracking-wider">Driver Status</span>
            <span className="font-bold text-emerald-400 text-xs mt-0.5 block">{driver.status || "AVAILABLE"}</span>
          </div>
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="text-slate-500 block text-[10px] font-semibold uppercase tracking-wider">Current Location</span>
            <span className="font-bold text-white text-xs mt-0.5 truncate block">{driver.current_location || "Location unavailable"}</span>
          </div>
        </div>

        {/* Coords detail */}
        {hasCoords ? (
          <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 font-mono flex items-center justify-between">
            <span>Verified Coordinates:</span>
            <span className="text-white font-semibold">{driver.latitude.toFixed(5)}, {driver.longitude.toFixed(5)}</span>
          </div>
        ) : (
          <div className="p-2.5 bg-rose-500/5 rounded-xl border border-rose-500/10 text-[11px] text-rose-400">
            Location unavailable (No verified coordinates)
          </div>
        )}

        {/* Key Particulars Table */}
        <div className="space-y-2 text-xs text-slate-300 pt-1">
          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">Phone:</span>
            <span className="font-semibold text-white">{driver.phone || "N/A"}</span>
          </div>

          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">Assigned Vehicle:</span>
            <span className="font-medium text-indigo-300 font-mono">
              {driver.active_vehicle ? driver.active_vehicle.registration_number : "Unassigned"}
            </span>
          </div>

          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">Assigned Shipment:</span>
            <span className="font-medium text-white font-mono">
              {driver.active_shipment ? driver.active_shipment.tracking_id : "None"}
            </span>
          </div>

          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">Last Updated:</span>
            <span className="font-mono text-slate-400">
              {driver.last_updated ? new Date(driver.last_updated).toLocaleTimeString() : "N/A"}
            </span>
          </div>

          <div className="flex justify-between py-1">
            <span className="text-slate-500">Source / Mode:</span>
            <span className="font-mono text-[11px] text-slate-400">{driver.source || "GPS Provider"} / {driver.mode || "live"}</span>
          </div>
        </div>
      </div>

      {/* Driver Location History Section */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 text-indigo-400" />
          <span>Driver Location History</span>
        </h4>

        <TrackingTimeline items={historyItems} emptyMessage="No GPS location history stored." />
      </div>
    </div>
  );
};
