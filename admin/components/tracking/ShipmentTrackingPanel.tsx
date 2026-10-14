"use client";

import React from "react";
import { Package, MapPin, User, Truck, Clock, ShieldCheck, AlertCircle } from "lucide-react";
import { TrackingTimeline, TimelineItem } from "./TrackingTimeline";

interface ShipmentTrackingPanelProps {
  shipment: any | null;
  isLoading?: boolean;
  error?: string | null;
}

export const ShipmentTrackingPanel: React.FC<ShipmentTrackingPanelProps> = ({
  shipment,
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-full min-h-[440px] flex flex-col items-center justify-center text-slate-500">
        <Package className="w-8 h-8 animate-bounce text-indigo-400 mb-2" />
        <span className="text-xs font-semibold">Loading shipment details...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-full min-h-[440px] flex flex-col items-center justify-center text-center p-6">
        <AlertCircle className="w-10 h-10 text-rose-500 mb-2" />
        <h4 className="text-sm font-bold text-white mb-1">Shipment Not Found</h4>
        <p className="text-xs text-rose-300 max-w-xs">{error}</p>
      </div>
    );
  }

  if (!shipment) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-full min-h-[440px] flex flex-col items-center justify-center text-center text-slate-500">
        <Package className="w-10 h-10 text-slate-700 mb-2" />
        <h4 className="text-sm font-bold text-slate-300 mb-1">No Shipment Selected</h4>
        <p className="text-xs text-slate-500 max-w-xs">
          Enter a valid Tracking ID (e.g. TLX-DEMO-100001) in the search box above to inspect details.
        </p>
      </div>
    );
  }

  // Format events for timeline
  const timelineItems: TimelineItem[] = (shipment.events || []).map((evt: any, idx: number) => ({
    id: evt.id || `evt-${idx}`,
    title: evt.event_type || evt.status || "LOCATION_UPDATED",
    description: evt.message || evt.description,
    location: evt.location || evt.city,
    latitude: evt.latitude,
    longitude: evt.longitude,
    timestamp: evt.timestamp || evt.created_at,
    isLatest: idx === 0,
  }));

  const currCoords = shipment.current_coordinates;
  const isMock = shipment.is_mock ?? true;
  const etaText = shipment.eta || "ETA unavailable";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 md:p-6 space-y-6 h-full overflow-y-auto max-h-[600px] shadow-xl">
      {/* Header Info */}
      <div className="border-b border-slate-800 pb-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Tracking ID</span>
            <h3 className="text-lg font-bold font-mono text-indigo-400 tracking-tight">{shipment.tracking_id}</h3>
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
            <span className="text-slate-500 block text-[10px] font-semibold uppercase tracking-wider">Status</span>
            <span className="font-bold text-indigo-300 text-xs mt-0.5 block">{shipment.status}</span>
          </div>
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="text-slate-500 block text-[10px] font-semibold uppercase tracking-wider">Location</span>
            <span className="font-bold text-emerald-400 text-xs mt-0.5 truncate block">{shipment.current_location || "Location unavailable"}</span>
          </div>
        </div>

        {/* Coords detail */}
        {currCoords ? (
          <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 font-mono flex items-center justify-between">
            <span>Coordinates:</span>
            <span className="text-white font-semibold">{currCoords.lat.toFixed(5)}, {currCoords.lng.toFixed(5)}</span>
          </div>
        ) : (
          <div className="p-2.5 bg-rose-500/5 rounded-xl border border-rose-500/10 text-[11px] text-rose-400">
            Location unavailable (No verified coordinates)
          </div>
        )}

        {/* Key Particulars Table */}
        <div className="space-y-2 text-xs text-slate-300 pt-1">
          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">Customer:</span>
            <span className="font-semibold text-white">{shipment.customer_name || "N/A"}</span>
          </div>

          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">Origin:</span>
            <span className="font-medium text-emerald-400">{shipment.origin || "N/A"}</span>
          </div>

          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">Destination:</span>
            <span className="font-medium text-rose-400">{shipment.destination || "N/A"}</span>
          </div>

          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">Driver:</span>
            <span className="font-medium text-indigo-300">{shipment.driver?.full_name || "Unassigned"}</span>
          </div>

          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">Vehicle:</span>
            <span className="font-medium text-white">{shipment.vehicle?.registration_number || "Unassigned"}</span>
          </div>

          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">ETA:</span>
            <span className="font-semibold text-indigo-300">{etaText}</span>
          </div>

          <div className="flex justify-between py-1 border-b border-slate-800/50">
            <span className="text-slate-500">Last Updated:</span>
            <span className="font-mono text-slate-400">
              {shipment.last_updated ? new Date(shipment.last_updated).toLocaleTimeString() : "N/A"}
            </span>
          </div>

          <div className="flex justify-between py-1">
            <span className="text-slate-500">Source / Mode:</span>
            <span className="font-mono text-[11px] text-slate-400">{shipment.source || "PostgreSQL"} / {shipment.mode || "live"}</span>
          </div>
        </div>
      </div>

      {/* Timeline Section */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-indigo-400" />
          <span>Tracking Timeline</span>
        </h4>

        <TrackingTimeline items={timelineItems} emptyMessage="No event history recorded yet." />
      </div>
    </div>
  );
};
