"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { MapPin, ShieldCheck, RefreshCw, Loader2, AlertTriangle } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";
import { TrackingSearch } from "@/components/tracking/TrackingSearch";
import { ShipmentTrackingPanel } from "@/components/tracking/ShipmentTrackingPanel";
import { DriverTrackingPanel } from "@/components/tracking/DriverTrackingPanel";

// Dynamically import Leaflet AdminTrackingMap with SSR disabled
const AdminTrackingMap = dynamic(
  () => import("@/components/tracking/AdminTrackingMap").then((mod) => mod.AdminTrackingMap),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full min-h-[440px] rounded-2xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center text-slate-500 text-xs">
        <Loader2 className="w-7 h-7 animate-spin text-indigo-400 mb-2" />
        <span>Loading Interactive Map Layer...</span>
      </div>
    ),
  }
);

export default function AdminTrackingPage() {
  const [activeTab, setActiveTab] = useState<"shipments" | "drivers">("shipments");

  // Map Controls State
  const [followEnabled, setFollowEnabled] = useState(true);

  // WebSocket Realtime State
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  // Monotonic request id so a slow response can never overwrite a newer search.
  const trackingRequestRef = useRef(0);

  // Shipment Tracking State
  // Starts empty on purpose: the previous default `TLX-DEMO-100001` presented
  // seeded demo data as if it were live operations.
  const [searchTrackingId, setSearchTrackingId] = useState("");
  const [shipmentData, setShipmentData] = useState<any | null>(null);
  const [isShipmentLoading, setIsShipmentLoading] = useState(false);
  const [shipmentError, setShipmentError] = useState<string | null>(null);

  // Driver Tracking State
  const [driverList, setDriverList] = useState<any[]>([]);
  const [selectedDriverId, setSelectedDriverId] = useState<string>("");
  const [driverData, setDriverData] = useState<any | null>(null);
  const [isDriverLoading, setIsDriverLoading] = useState(false);
  const [driverError, setDriverError] = useState<string | null>(null);

  // 1. Fetch Shipment Tracking Data
  const handleFetchShipmentTracking = useCallback(async (idToSearch?: string) => {
    const targetId = (idToSearch || searchTrackingId).trim();
    if (!targetId) return;

    const requestId = ++trackingRequestRef.current;
    setIsShipmentLoading(true);
    setShipmentError(null);
    try {
      const res = await adminApiClient.get<any>(`/admin/tracking/shipments/${targetId}`);
      if (requestId !== trackingRequestRef.current) return;
      if (res && res.success && res.tracking) {
        setShipmentData(res.tracking);
      } else {
        throw new Error(res.message || `Consignment tracking '${targetId}' not found.`);
      }
    } catch (err: any) {
      if (requestId !== trackingRequestRef.current) return;
      setShipmentError(err.message || "Failed to fetch shipment tracking details from backend database.");
      setShipmentData(null);
    } finally {
      if (requestId === trackingRequestRef.current) {
        setIsShipmentLoading(false);
      }
    }
  }, [searchTrackingId]);

  // 2. Fetch Fleet Drivers List & Selected Driver Data
  const fetchDriverList = useCallback(async () => {
    try {
      const res = await adminApiClient.get<any>("/admin/drivers");
      if (res && res.success && res.drivers) {
        setDriverList(res.drivers);
        if (res.drivers.length > 0 && !selectedDriverId) {
          const firstDrvId = res.drivers[0].driver_id;
          setSelectedDriverId(firstDrvId);
          handleFetchDriverTracking(firstDrvId);
        }
      }
    } catch (err: any) {
      // Handled silently
    }
  }, [selectedDriverId]);

  const handleFetchDriverTracking = useCallback(async (driverIdToFetch: string) => {
    if (!driverIdToFetch) return;
    setIsDriverLoading(true);
    setDriverError(null);
    try {
      const res = await adminApiClient.get<any>(`/admin/tracking/drivers/${driverIdToFetch}`);
      if (res && res.success && res.driver_tracking) {
        setDriverData(res.driver_tracking);
      } else {
        throw new Error(res.message || "Driver tracking telemetry not found.");
      }
    } catch (err: any) {
      setDriverError(err.message || "Failed to fetch driver tracking details.");
      setDriverData(null);
    } finally {
      setIsDriverLoading(false);
    }
  }, []);

  // Initial Load
  useEffect(() => {
    /**
     * Load the real list of trackable consignments and open the most recent one.
     * Nothing is fetched from a hardcoded demo tracking id on mount.
     */
    let cancelled = false;
    const loadInitialData = async () => {
      try {
        const res = await adminApiClient.get<any>("/admin/tracking/shipments");
        if (cancelled) return;
        const list: any[] = res?.shipments || [];
        const first = list[0];
        const firstId = first?.tracking_id || first?.trackingId;
        if (firstId) {
          setSearchTrackingId(firstId);
          handleFetchShipmentTracking(firstId);
        }
      } catch (err: any) {
        if (!cancelled) {
          setShipmentError(err.message || "Failed to load the trackable shipments list.");
        }
      }
      if (!cancelled) fetchDriverList();
    };
    loadInitialData();
    return () => {
      cancelled = true;
    };
  }, []);

  // WebSocket Connection Setup for Realtime Location Updates
  useEffect(() => {
    /**
     * Build the socket URL from NEXT_PUBLIC_API_URL instead of hardcoding
     * `ws://localhost:8000`: a hardcoded `ws://` is blocked as mixed content on
     * any HTTPS deployment, and the port is not necessarily 8000.
     * The admin socket requires a valid admin token in the query string.
     */
    const wsUrl = adminApiClient.buildWsUrl("/realtime/ws/admin/all");

    let socket: WebSocket | null = null;
    let reconnectTimer: any = null;
    let disposed = false;

    const connectWebSocket = () => {
      if (disposed) return;
      try {
        socket = new WebSocket(wsUrl);
        socketRef.current = socket;

        socket.onopen = () => {
          setIsConnected(true);
        };

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (!data) return;

            // Handle shipment.location_changed event
            if (data.event === "shipment.location_changed" || data.event_type === "shipment.location_changed") {
              const payloadId = data.tracking_id || data.shipment_id;
              setShipmentData((prev: any) => {
                if (!prev || (prev.tracking_id !== payloadId && prev.id !== payloadId)) return prev;

                const newLat = typeof data.latitude === "number" ? data.latitude : prev.current_coordinates?.lat;
                const newLng = typeof data.longitude === "number" ? data.longitude : prev.current_coordinates?.lng;

                const newEvent = {
                  id: `evt-ws-${Date.now()}`,
                  event_type: data.status || "LOCATION_UPDATED",
                  message: data.message || `Location updated to ${data.location || data.location_name}`,
                  location: data.location || data.location_name || prev.current_location,
                  latitude: newLat,
                  longitude: newLng,
                  timestamp: data.timestamp || new Date().toISOString(),
                };

                return {
                  ...prev,
                  current_location: data.location || data.location_name || prev.current_location,
                  status: data.status || prev.status,
                  last_updated: data.timestamp || new Date().toISOString(),
                  is_mock: data.is_mock ?? prev.is_mock,
                  mode: data.mode || prev.mode,
                  current_coordinates: newLat && newLng ? { lat: newLat, lng: newLng } : prev.current_coordinates,
                  events: [newEvent, ...(prev.events || [])],
                };
              });
            }

            // Handle driver.location_changed event
            if (data.event === "driver.location_changed" || data.event_type === "driver.location_changed") {
              const payloadDriverId = data.driver_id;
              setDriverData((prev: any) => {
                if (!prev || prev.driver_id !== payloadDriverId) return prev;

                const newLat = typeof data.latitude === "number" ? data.latitude : prev.latitude;
                const newLng = typeof data.longitude === "number" ? data.longitude : prev.longitude;

                const newLocItem = {
                  id: `loc-ws-${Date.now()}`,
                  location_name: data.location_name || data.location || prev.current_location,
                  latitude: newLat,
                  longitude: newLng,
                  source: data.source || "realtime_websocket",
                  recorded_at: data.timestamp || new Date().toISOString(),
                };

                return {
                  ...prev,
                  current_location: data.location_name || data.location || prev.current_location,
                  status: data.status || prev.status,
                  latitude: newLat,
                  longitude: newLng,
                  last_updated: data.timestamp || new Date().toISOString(),
                  is_mock: data.is_mock ?? prev.is_mock,
                  mode: data.mode || prev.mode,
                  location_history: [newLocItem, ...(prev.location_history || [])],
                };
              });
            }
          } catch (e) {
            // Ignore parse errors
          }
        };

        socket.onclose = () => {
          setIsConnected(false);
          if (!disposed) {
            reconnectTimer = setTimeout(connectWebSocket, 4000);
          }
        };

        socket.onerror = () => {
          setIsConnected(false);
        };
      } catch (e) {
        setIsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      disposed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      const active = socketRef.current;
      socketRef.current = null;
      if (active) {
        active.onclose = null;
        active.onerror = null;
        active.onmessage = null;
        active.close();
      }
    };
  }, []);

  const handleManualRefresh = () => {
    if (activeTab === "shipments") {
      handleFetchShipmentTracking();
    } else {
      handleFetchDriverTracking(selectedDriverId);
    }
  };

  // Prepare Map Props for Shipment Tab
  const getShipmentMapProps = () => {
    if (!shipmentData) return { markers: [], routePoints: [], isLocationAvailable: false, isRouteAvailable: false };

    const markers: any[] = [];
    const origCoords = shipmentData.origin_coordinates;
    const destCoords = shipmentData.destination_coordinates;
    const currCoords = shipmentData.current_coordinates;

    if (origCoords) {
      markers.push({
        id: "origin",
        lat: origCoords.lat,
        lng: origCoords.lng,
        title: `Origin: ${shipmentData.origin}`,
        type: "origin",
      });
    }

    if (destCoords) {
      markers.push({
        id: "destination",
        lat: destCoords.lat,
        lng: destCoords.lng,
        title: `Destination: ${shipmentData.destination}`,
        type: "destination",
      });
    }

    if (currCoords) {
      markers.push({
        id: "current",
        lat: currCoords.lat,
        lng: currCoords.lng,
        title: `Shipment: ${shipmentData.tracking_id}`,
        subtitle: `Current: ${shipmentData.current_location}`,
        type: "current",
        details: {
          status: shipmentData.status,
          mode: shipmentData.is_mock ? "DEMO DATA" : "LIVE",
          last_updated: shipmentData.last_updated,
        },
      });
    }

    const routePoints: [number, number][] = shipmentData.route_points || [];

    return {
      markers,
      routePoints,
      isLocationAvailable: Boolean(currCoords || origCoords || destCoords),
      isRouteAvailable: routePoints.length >= 2,
    };
  };

  // Prepare Map Props for Driver Tab
  const getDriverMapProps = () => {
    if (!driverData) return { markers: [], routePoints: [], isLocationAvailable: false, isRouteAvailable: false };

    const markers: any[] = [];
    const trailPoints: [number, number][] = [];

    const history = driverData.location_history || [];

    history.forEach((loc: any, idx: number) => {
      if (typeof loc.latitude === "number" && typeof loc.longitude === "number") {
        const isLatest = idx === 0;
        trailPoints.push([loc.latitude, loc.longitude]);

        if (isLatest) {
          markers.push({
            id: `driver-${loc.id || idx}`,
            lat: loc.latitude,
            lng: loc.longitude,
            title: `Driver: ${driverData.full_name}`,
            subtitle: `Location: ${loc.location_name || driverData.current_location}`,
            type: "driver",
            details: {
              status: driverData.status,
              mode: driverData.is_mock ? "DEMO DATA" : "LIVE",
              last_updated: loc.recorded_at || driverData.last_updated,
            },
          });
        }
      }
    });

    if (markers.length === 0 && typeof driverData.latitude === "number" && typeof driverData.longitude === "number") {
      markers.push({
        id: `driver-main`,
        lat: driverData.latitude,
        lng: driverData.longitude,
        title: `Driver: ${driverData.full_name}`,
        subtitle: `Location: ${driverData.current_location}`,
        type: "driver",
        details: {
          status: driverData.status,
          mode: driverData.is_mock ? "DEMO DATA" : "LIVE",
          last_updated: driverData.last_updated,
        },
      });
    }

    return {
      markers,
      routePoints: trailPoints.reverse(),
      isLocationAvailable: markers.length > 0,
      isRouteAvailable: trailPoints.length >= 2,
    };
  };

  const activeMapProps = activeTab === "shipments" ? getShipmentMapProps() : getDriverMapProps();
  const currentIsMock = activeTab === "shipments" ? shipmentData?.is_mock : driverData?.is_mock;
  const currentDataMode = activeTab === "shipments" ? shipmentData?.mode : driverData?.mode;

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto p-4 md:p-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <MapPin className="w-6 h-6 text-indigo-400 shrink-0" />
            <span>Google Maps-Style Live Tracking</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time interactive fleet driver &amp; consignment tracking console powered by Google Maps API &amp; WebSocket telemetry.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-900 text-slate-300 border border-slate-800 text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span>Admin Control Panel</span>
          </div>
        </div>
      </div>

      {/* Control & Search Bar */}
      <TrackingSearch
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        searchTrackingId={searchTrackingId}
        setSearchTrackingId={setSearchTrackingId}
        onSearchShipment={handleFetchShipmentTracking}
        isShipmentLoading={isShipmentLoading}
        driverList={driverList}
        selectedDriverId={selectedDriverId}
        setSelectedDriverId={setSelectedDriverId}
        onSearchDriver={handleFetchDriverTracking}
        isDriverLoading={isDriverLoading}
        followEnabled={followEnabled}
        setFollowEnabled={setFollowEnabled}
        onRefresh={handleManualRefresh}
        isConnected={isConnected}
        isMockData={currentIsMock}
        dataMode={currentDataMode}
      />

      {/* Errors display */}
      {activeTab === "shipments" && shipmentError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{shipmentError}</span>
        </div>
      )}

      {activeTab === "drivers" && driverError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{driverError}</span>
        </div>
      )}

      {/* Main Map + Right Side Tracking Details Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Large Interactive Map (Takes 2 cols) */}
        <div className="lg:col-span-2 h-[560px] lg:h-[620px] rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950">
          <AdminTrackingMap
            markers={activeMapProps.markers}
            routePoints={activeMapProps.routePoints}
            isLocationAvailable={activeMapProps.isLocationAvailable}
            isRouteAvailable={activeMapProps.isRouteAvailable}
            followEnabled={followEnabled}
          />
        </div>

        {/* Tracking Details & Event History Panel (Takes 1 col) */}
        <div className="lg:col-span-1 h-[560px] lg:h-[620px]">
          {activeTab === "shipments" ? (
            <ShipmentTrackingPanel
              shipment={shipmentData}
              isLoading={isShipmentLoading}
              error={shipmentError}
            />
          ) : (
            <DriverTrackingPanel
              driver={driverData}
              isLoading={isDriverLoading}
              error={driverError}
            />
          )}
        </div>
      </div>
    </div>
  );
}
