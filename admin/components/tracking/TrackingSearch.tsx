"use client";

import React from "react";
import { Search, RefreshCw, Loader2, Navigation, Package, Truck } from "lucide-react";
import { RealtimeIndicator } from "./RealtimeIndicator";

interface TrackingSearchProps {
  activeTab: "shipments" | "drivers";
  setActiveTab: (tab: "shipments" | "drivers") => void;
  
  // Shipment search
  searchTrackingId: string;
  setSearchTrackingId: (id: string) => void;
  onSearchShipment: (id?: string) => void;
  isShipmentLoading: boolean;

  // Driver search
  driverList: any[];
  selectedDriverId: string;
  setSelectedDriverId: (id: string) => void;
  onSearchDriver: (driverId: string) => void;
  isDriverLoading: boolean;

  // Controls
  followEnabled: boolean;
  setFollowEnabled: (val: boolean | ((prev: boolean) => boolean)) => void;
  onRefresh: () => void;
  
  // Socket & data mode
  isConnected: boolean;
  isMockData?: boolean;
  dataMode?: string;
}

export const TrackingSearch: React.FC<TrackingSearchProps> = ({
  activeTab,
  setActiveTab,
  searchTrackingId,
  setSearchTrackingId,
  onSearchShipment,
  isShipmentLoading,
  driverList,
  selectedDriverId,
  setSelectedDriverId,
  onSearchDriver,
  isDriverLoading,
  followEnabled,
  setFollowEnabled,
  onRefresh,
  isConnected,
  isMockData = false,
  dataMode = "live",
}) => {
  const isLoading = activeTab === "shipments" ? isShipmentLoading : isDriverLoading;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 space-y-4 shadow-xl">
      {/* Top Row: Tabs + Realtime Connection Status + Refresh */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        {/* Navigation Tabs */}
        <div className="flex items-center space-x-2 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab("shipments")}
            className={`px-4 py-2 text-xs font-bold rounded-lg flex items-center space-x-2 transition-all ${
              activeTab === "shipments"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            <Package className="w-3.5 h-3.5" />
            <span>SHIPMENT TRACKING</span>
          </button>

          <button
            onClick={() => setActiveTab("drivers")}
            className={`px-4 py-2 text-xs font-bold rounded-lg flex items-center space-x-2 transition-all ${
              activeTab === "drivers"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            <Truck className="w-3.5 h-3.5" />
            <span>DRIVER TRACKING</span>
          </button>
        </div>

        {/* Realtime Status Indicator & Actions */}
        <div className="flex items-center space-x-3">
          <RealtimeIndicator
            isConnected={isConnected}
            isMock={isMockData}
            mode={dataMode}
          />

          {/* Follow / Center Toggle */}
          <button
            onClick={() => setFollowEnabled((prev) => !prev)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              followEnabled
                ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/30 shadow-sm"
                : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
            }`}
            title="Auto-center map on latest verified coordinates"
          >
            <Navigation className={`w-3.5 h-3.5 ${followEnabled ? "text-indigo-400" : ""}`} />
            <span>{followEnabled ? "Following" : "Follow"}</span>
          </button>

          {/* Refresh Control */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="px-3.5 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-200 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 disabled:opacity-50"
            title="Fetch fresh data from backend"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Bottom Row: Context-Specific Search Inputs */}
      {activeTab === "shipments" ? (
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
            <input
              type="text"
              value={searchTrackingId}
              onChange={(e) => setSearchTrackingId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onSearchShipment()}
              placeholder="Search Tracking ID (e.g. TLX-DEMO-100001 or TLX-2026-100001)..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white font-mono placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
            />
          </div>
          <button
            onClick={() => onSearchShipment()}
            disabled={isShipmentLoading}
            className="w-full sm:w-auto px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl shadow-md shadow-indigo-600/20 disabled:opacity-50 flex items-center justify-center space-x-2 transition-all shrink-0"
          >
            {isShipmentLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            <span>SEARCH SHIPMENT</span>
          </button>
        </div>
      ) : (
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full flex items-center">
            <Truck className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
            <select
              value={selectedDriverId}
              onChange={(e) => {
                setSelectedDriverId(e.target.value);
                onSearchDriver(e.target.value);
              }}
              className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all appearance-none"
            >
              <option value="" disabled>Select Driver...</option>
              {driverList.map((d) => (
                <option key={d.id || d.driver_id} value={d.driver_id}>
                  {d.full_name} ({d.driver_id}) — {d.status}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={() => onSearchDriver(selectedDriverId)}
            disabled={isDriverLoading || !selectedDriverId}
            className="w-full sm:w-auto px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl shadow-md shadow-indigo-600/20 disabled:opacity-50 flex items-center justify-center space-x-2 transition-all shrink-0"
          >
            {isDriverLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            <span>INSPECT DRIVER</span>
          </button>
        </div>
      )}
    </div>
  );
};
