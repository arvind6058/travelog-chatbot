"use client";

import React, { useState, useEffect } from "react";
import { Package, Truck, MapPin, Radio, ShieldCheck, Clock, RefreshCw, AlertCircle, UserCheck } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface TrackingResultCardProps {
  data: any;
  trackingId?: string;
}

export const TrackingResultCard: React.FC<TrackingResultCardProps> = ({ data, trackingId }) => {
  const [liveData, setLiveData] = useState(data);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    setLiveData(data);
  }, [data]);

  const tId = trackingId || liveData?.tracking_id || liveData?.data?.tracking_id;

  useEffect(() => {
    if (!tId) return;
    const socketPath = `/realtime/ws/tracking/${encodeURIComponent(tId)}`;
    // Scheme and host come from NEXT_PUBLIC_API_URL, so HTTPS deployments get
    // `wss:` instead of a hardcoded `ws://host:8000` (mixed content).
    // The tracking channel is public, so no token is required here.
    const wsUrl = apiClient.buildWsUrl(socketPath);
    let socket: WebSocket | null = null;
    let cancelled = false;

    try {
      socket = new WebSocket(wsUrl);
      socket.onopen = () => {
        if (!cancelled) setWsConnected(true);
      };
      socket.onmessage = (evt) => {
        if (cancelled) return;
        try {
          const update = JSON.parse(evt.data);
          if (update.status || update.location) {
            setLiveData((prev: any) => ({
              ...prev,
              status: update.status || prev?.status,
              verified_location: update.location || prev?.verified_location || prev?.current_location,
              current_location: update.location || prev?.current_location || prev?.verified_location,
              events: update.message ? [...(prev?.events || []), {
                status: update.status || "UPDATE",
                location: update.location || "",
                message: update.message,
                timestamp: update.timestamp || new Date().toISOString()
              }] : (prev?.events || [])
            }));
          }
        } catch (e) {
          // parse error
        }
      };
      socket.onclose = () => {
        if (!cancelled) setWsConnected(false);
      };
      socket.onerror = () => {
        if (!cancelled) setWsConnected(false);
      };
    } catch (e) {
      setWsConnected(false);
    }

    return () => {
      // Always close, even while CONNECTING: under React StrictMode the first
      // socket is still handshaking when this cleanup runs, so gating the close
      // on readyState === OPEN orphaned it and it kept calling setState after
      // unmount.
      cancelled = true;
      const active = socket;
      socket = null;
      if (active) {
        active.onopen = null;
        active.onmessage = null;
        active.onclose = null;
        active.onerror = null;
        try {
          active.close();
        } catch (e) {
          // Closing an already-failed socket is not an error worth surfacing.
        }
      }
    };
  }, [tId]);

  const handleRefresh = async () => {
    if (!tId || isRefreshing) return;
    setIsRefreshing(true);
    try {
      /**
       * Refresh through the tracking endpoint used for the initial lookup —
       * the same full tracking shape the card was built from. The admin-style
       * shipment record has no `current_location`/driver/vehicle, so using it
       * here made every manual refresh visibly regress the card.
       */
      const res = await apiClient.get<any>(`/shipments/${encodeURIComponent(tId)}`);
      const shipment = res?.shipment;
      if (shipment) {
        setLiveData((prev: any) => ({
          ...prev,
          found: true,
          tracking_id: shipment.tracking_id ?? prev?.tracking_id ?? tId,
          status: shipment.status ?? prev?.status,
          origin: shipment.origin ?? prev?.origin,
          destination: shipment.destination ?? prev?.destination,
          verified_location:
            shipment.current_location ?? prev?.verified_location ?? prev?.current_location,
          current_location:
            shipment.current_location ?? prev?.current_location ?? prev?.verified_location,
          expected_delivery_date: shipment.expected_delivery_date ?? prev?.expected_delivery_date,
          pickup_date: shipment.pickup_date ?? prev?.pickup_date,
          cost_inr: shipment.cost_inr ?? prev?.cost_inr,
          weight_kg: shipment.weight_kg ?? prev?.weight_kg,
          is_demo: shipment.is_demo ?? prev?.is_demo,
          // Only replace collections when the response actually carries them,
          // so a partial public view cannot wipe driver/vehicle details.
          events: Array.isArray(res?.events) ? res.events : prev?.events || [],
          driver: res?.driver ?? prev?.driver,
          vehicle: res?.vehicle ?? prev?.vehicle,
          last_updated: new Date().toISOString()
        }));
      } else {
        setLiveData((prev: any) => ({
          ...prev,
          found: false,
          status: prev?.status === "NOT_FOUND" ? prev.status : "NOT_FOUND",
          refresh_error: "No shipment record found for this tracking ID.",
        }));
      }
    } catch (err: any) {
      setLiveData((prev: any) => ({
        ...prev,
        refresh_error: err?.message || "Failed to refresh tracking data.",
      }));
    } finally {
      setIsRefreshing(false);
    }
  };

  if (!tId) return null;

  const isFound = liveData?.found !== false && liveData?.status !== "NOT_FOUND";
  if (!isFound) {
    return (
      <div className="mt-3 p-3.5 rounded-xl bg-slate-950 border border-red-900/40 text-red-300 font-sans text-xs space-y-2">
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span className="font-mono font-bold text-red-200">Shipment {tId} Not Found</span>
        </div>
        <p className="text-[11px] text-red-300/80">
          No shipment record exists for <code className="font-mono text-white">{tId}</code> in TravelLogix backend database. Please check your tracking number.
        </p>
      </div>
    );
  }

  const status = liveData?.status || "REGISTERED";
  const origin = liveData?.origin || "Origin Hub";
  const destination = liveData?.destination || "Destination Hub";
  const verifiedLocation = liveData?.verified_location || liveData?.current_location || origin || "LOCATION UNAVAILABLE";
  const isMock =
    liveData?.provenance?.is_mock ??
    liveData?.is_mock ??
    liveData?.is_demo ??
    liveData?.shipment?.is_demo ??
    (liveData?.provenance?.mode === "demo");
  const events = liveData?.events || [];
  const driverName = liveData?.driver?.full_name || liveData?.driver_name;
  const vehicleNo = liveData?.vehicle?.registration_number || liveData?.vehicle?.vehicle_number || liveData?.vehicle_number;
  const eta = liveData?.expected_delivery_date;
  const lastUpdated = liveData?.last_updated || liveData?.provenance?.fetched_at;

  return (
    <div className="mt-3 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 font-sans text-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center space-x-2">
          <Package className="w-4 h-4 text-sky-400 shrink-0" />
          <span className="font-mono font-bold text-sky-300">{tId}</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-sky-300 transition-colors"
            title="Refresh Tracking Data"
          >
            <RefreshCw className={`w-3 h-3 ${isRefreshing ? "animate-spin text-sky-400" : ""}`} />
          </button>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
            isMock
              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
              : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
          }`}>
            {isMock ? "DEMO DATA" : (liveData?.provenance?.mode === "live" ? "LIVE" : "LATEST UPDATE")}
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20">
            {status}
          </span>
        </div>
      </div>

      {/* Route & Location */}
      <div className="grid grid-cols-2 gap-2 text-slate-300">
        <div>
          <span className="text-[10px] text-slate-500 block uppercase font-semibold">Route</span>
          <span className="font-medium">{origin} &rarr; {destination}</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block uppercase font-semibold">Current / Verified Location</span>
          <span className="font-medium text-emerald-400 flex items-center gap-1">
            <MapPin className="w-3 h-3 shrink-0" />
            <span className="truncate">{verifiedLocation}</span>
          </span>
        </div>
      </div>

      {/* Refresh failure (non-fatal: the last known card stays visible) */}
      {liveData?.refresh_error && (
        <div className="flex items-start space-x-1.5 text-[11px] text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-lg px-2.5 py-1.5">
          <AlertCircle className="w-3 h-3 shrink-0 mt-0.5" />
          <span>{liveData.refresh_error}</span>
        </div>
      )}

      {/* Optional Driver & Vehicle & ETA Details */}
      {(driverName || vehicleNo || eta) && (
        <div className="grid grid-cols-2 gap-2 text-slate-300 pt-2 border-t border-slate-900">
          {driverName && (
            <div>
              <span className="text-[10px] text-slate-500 block uppercase font-semibold">Driver</span>
              <span className="font-medium text-slate-200 flex items-center gap-1">
                <UserCheck className="w-3 h-3 text-sky-400 shrink-0" />
                <span>{driverName}</span>
              </span>
            </div>
          )}
          {vehicleNo && (
            <div>
              <span className="text-[10px] text-slate-500 block uppercase font-semibold">Vehicle</span>
              <span className="font-medium text-slate-200 flex items-center gap-1">
                <Truck className="w-3 h-3 text-sky-400 shrink-0" />
                <span>{vehicleNo}</span>
              </span>
            </div>
          )}
          {eta && (
            <div className="col-span-2">
              <span className="text-[10px] text-slate-500 block uppercase font-semibold">Estimated Delivery (ETA)</span>
              <span className="font-medium text-sky-300">{eta}</span>
            </div>
          )}
        </div>
      )}

      {/* Milestone Events History for THIS Tracking ID */}
      {events.length > 0 && (
        <div className="pt-2 border-t border-slate-800/80 space-y-1">
          <span className="text-[10px] text-slate-500 uppercase font-semibold block">Shipment History</span>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {events.map((e: any, idx: number) => (
              <div key={idx} className="flex items-start space-x-1.5 text-[11px] text-slate-400">
                <Clock className="w-3 h-3 text-sky-400 shrink-0 mt-0.5" />
                <span><strong className="text-slate-200">{e.status}:</strong> {e.message || e.location}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Realtime Subscription Footer */}
      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500">
        <div className="flex items-center space-x-1.5">
          <Radio className={`w-3 h-3 ${wsConnected ? "text-emerald-400 animate-pulse" : "text-slate-600"}`} />
          <span>{wsConnected ? "Realtime stream active" : "Polling / Stream ready"}</span>
        </div>
        <div className="flex items-center space-x-1">
          <ShieldCheck className="w-3 h-3 text-sky-400" />
          <span>{lastUpdated ? `Updated ${new Date(lastUpdated).toLocaleTimeString()}` : "Verified Database"}</span>
        </div>
      </div>
    </div>
  );
};

