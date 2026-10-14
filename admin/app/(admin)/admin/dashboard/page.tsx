"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Package,
  Truck,
  Users,
  AlertTriangle,
  CheckCircle,
  Clock,
  PlusCircle,
  Activity,
  Loader2,
  RefreshCw,
  MessageSquare,
} from "lucide-react";
import { adminApiClient } from "@/lib/api-client";

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState({
    totalShipments: 0,
    registered: 0,
    inTransit: 0,
    outForDelivery: 0,
    delivered: 0,
    delayed: 0,
    availableDrivers: 0,
    driversOnDelivery: 0,
    activeVehicles: 0,
    customerCount: 0,
    totalConversations: 0,
  });

  const [recentShipments, setRecentShipments] = useState<any[]>([]);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminApiClient.get<any>("/admin/dashboard");
      if (res && res.success) {
        setMetrics(res.metrics || {});
        setRecentShipments(res.recentShipments || []);
        setRecentEvents(res.recentEvents || []);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load dashboard metrics from backend.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Operations Dashboard</span>
            {isLoading && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
          </h1>
          <p className="text-xs text-slate-400 mt-1">Real-time logistics monitoring and fleet deployment</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDashboardData}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
          </button>
          <Link
            href="/admin/shipments/new"
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 text-white font-medium text-xs shadow-md shadow-indigo-500/20 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Register New Shipment</span>
          </Link>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Total Shipments</span>
            <Package className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-600" /> : metrics.totalShipments}
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">In Transit</span>
            <Clock className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-600" /> : metrics.inTransit}
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Delivered</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-600" /> : metrics.delivered}
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Delayed</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-600" /> : metrics.delayed}
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Available Drivers</span>
            <Users className="w-4 h-4 text-violet-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-600" /> : metrics.availableDrivers}
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">AI Conversations</span>
            <MessageSquare className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-600" /> : metrics.totalConversations}
          </div>
        </div>
      </div>

      {/* Two Column Layout for Recent Shipments & Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Shipments */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white">Recent Shipments</h3>
            <Link href="/admin/shipments" className="text-xs text-indigo-400 hover:text-indigo-300">
              View All
            </Link>
          </div>

          {isLoading ? (
            <div className="py-12 text-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              <p className="text-xs">Fetching database shipments...</p>
            </div>
          ) : recentShipments.length === 0 ? (
            <div className="py-12 text-center text-slate-500">
              <Package className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="text-xs">No registered shipments yet</p>
              <p className="text-[11px] text-slate-600 mt-0.5">Use &apos;+ Register New Shipment&apos; to create your first order.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentShipments.map((s, i) => (
                <div key={i} className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-mono font-semibold text-indigo-300 block">{s.trackingId}</span>
                    <span className="text-slate-400 text-[11px]">{s.customer} &bull; {s.origin} &rarr; {s.destination}</span>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    {s.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Tracking Events */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white">Recent Telemetry & Audit Activity</h3>
            <Link href="/admin/tracking" className="text-xs text-indigo-400 hover:text-indigo-300">
              Live Monitor
            </Link>
          </div>

          {isLoading ? (
            <div className="py-12 text-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              <p className="text-xs">Fetching telemetry events...</p>
            </div>
          ) : recentEvents.length === 0 ? (
            <div className="py-12 text-center text-slate-500">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="text-xs">No live telemetry events recorded</p>
              <p className="text-[11px] text-slate-600 mt-0.5">Verified milestone updates will stream here automatically.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentEvents.map((e, i) => (
                <div key={i} className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-slate-200 block">{e.title}</span>
                    <span className="text-slate-400 text-[11px]">{e.location} &bull; {e.trackingId}</span>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    {e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : ""}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
