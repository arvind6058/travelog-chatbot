"use client";

import React, { useState } from "react";
import Link from "next/link";
import { PlusCircle, Search, Package, Loader2, RefreshCw, Truck } from "lucide-react";
import { apiClient } from "@/lib/api-client";

export default function LogisticsHubPage() {
  const [trackingId, setTrackingId] = useState("");
  const [searchResult, setSearchResult] = useState<any | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [isTracking, setIsTracking] = useState(false);

  /** Real backend lookup for a single consignment (no invented telemetry). */
  const trackShipment = async (rawId: string) => {
    const id = rawId.trim().toUpperCase();
    setSearchError(null);
    setSearchResult(null);

    if (!id) {
      setSearchError("Please enter a tracking ID.");
      return;
    }

    if (!id.startsWith("TLX-")) {
      setSearchError("Please enter a valid tracking ID format (e.g. TLX-2026-12345678).");
      return;
    }

    setIsTracking(true);
    try {
      // Public tracking endpoint: returns the sanitized public view with the
      // shipment record and its milestone events.
      const res = await apiClient.get<any>(`/shipments/${encodeURIComponent(id)}`);
      if (res && res.success && res.shipment) {
        setSearchResult({ ...res.shipment, events: res.events || [] });
      } else {
        setSearchError(`No shipment record found for '${id}'. Please check your tracking number.`);
      }
    } catch (err: any) {
      if (err?.code === "HTTP_404") {
        setSearchError(`No shipment record found for '${id}'. Please check your tracking number.`);
      } else {
        setSearchError(err?.message || "Failed to reach the tracking service. Please try again.");
      }
    } finally {
      setIsTracking(false);
    }
  };

  const handleTrack = (e: React.FormEvent) => {
    e.preventDefault();
    trackShipment(trackingId);
  };

  // A tracking id may arrive from the shipments list as /logistics?track=TLX-...
  const prefillRef = React.useRef(false);
  React.useEffect(() => {
    if (prefillRef.current || typeof window === "undefined") return;
    prefillRef.current = true;
    const trackParam = new URLSearchParams(window.location.search).get("track");
    if (trackParam) {
      setTrackingId(trackParam);
      trackShipment(trackParam);
    }
  }, []);

  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner & Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Customer Logistics Hub</h1>
          <p className="text-sm text-slate-400 mt-1">Manage, register, and track your courier & freight consignments</p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            href="/logistics/register"
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-medium text-sm shadow-md shadow-sky-500/20 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Register New Shipment</span>
          </Link>
          <Link
            href="/shipments"
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 font-medium text-sm transition-all"
          >
            <Package className="w-4 h-4 text-sky-400" />
            <span>My Shipments</span>
          </Link>
        </div>
      </div>

      {/* Track Shipment Panel */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur-sm">
        <div className="max-w-2xl">
          <div className="flex items-center space-x-2 text-sky-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <Truck className="w-4 h-4" />
            <span>Instant Telemetry Tracking</span>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Track Shipment</h2>
          <p className="text-sm text-slate-400 mb-6">
            Enter your Travelogix tracking number to view real-time location checkpoints, assigned carrier status, and delivery milestones.
          </p>

          <form onSubmit={handleTrack} className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={trackingId}
              onChange={(e) => setTrackingId(e.target.value)}
              placeholder="e.g. TLX-2026-89472910"
              className="flex-1 px-4 py-3 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm font-mono"
            />
            <button
              type="submit"
              disabled={isTracking}
              className="px-6 py-3 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-semibold text-sm transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              {isTracking ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              <span>{isTracking ? "Tracking..." : "Track"}</span>
            </button>
          </form>

          {searchError && (
            <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start justify-between gap-3">
              <span>{searchError}</span>
              <button
                type="button"
                onClick={() => trackShipment(trackingId)}
                className="shrink-0 inline-flex items-center space-x-1 text-[11px] font-semibold text-rose-200 hover:text-white transition-colors"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Retry</span>
              </button>
            </div>
          )}

          {isTracking && !searchResult && (
            <div className="mt-6 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
              <span>Querying live consignment telemetry from the Travelogix database...</span>
            </div>
          )}

          {searchResult && (
            <div className="mt-6 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono text-sky-400 font-semibold">{searchResult.tracking_id}</span>
                <div className="flex items-center space-x-2">
                  {searchResult.is_demo && (
                    <span className="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                      DEMO DATA
                    </span>
                  )}
                  <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
                    {searchResult.status}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 pt-2 border-t border-slate-900">
                <div>Origin: {searchResult.origin}</div>
                <div>Destination: {searchResult.destination}</div>
                <div>Current location: {searchResult.current_location || "Awaiting first checkpoint"}</div>
                <div>Expected delivery: {searchResult.expected_delivery_date || "Not scheduled"}</div>
              </div>

              {Array.isArray(searchResult.events) && searchResult.events.length > 0 && (
                <div className="pt-2 border-t border-slate-900 space-y-1">
                  <span className="text-[10px] uppercase font-semibold text-slate-500 block">Milestones</span>
                  {searchResult.events.map((ev: any, i: number) => (
                    <div key={i} className="text-[11px] text-slate-400">
                      <strong className="text-slate-200">{ev.status || ev.event_type}:</strong>{" "}
                      {ev.message || ev.location || ""}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
