"use client";

import React, { useState, useEffect } from "react";
import { FileText, Loader2, RefreshCw, BarChart2, CheckCircle2, AlertTriangle } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";

export default function AdminReportsPage() {
  const [reportData, setReportData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchReports = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminApiClient.get<any>("/admin/reports");
      if (res && res.success) {
        setReportData(res.summary);
      } else {
        setErrorMsg("The backend did not return a report summary.");
      }
    } catch (e: any) {
      // A failed fetch must not render as a blank report page.
      setErrorMsg(e?.message || "Failed to generate reports from backend.");
      setReportData(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <FileText className="w-6 h-6 text-indigo-400" />
            <span>Logistics Operational Reports</span>
            {isLoading && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Database-backed operational summary metrics calculated from PostgreSQL records
          </p>
        </div>

        <button
          onClick={fetchReports}
          disabled={isLoading}
          className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
          title="Refresh Reports"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between gap-3">
          <span className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </span>
          <button
            onClick={fetchReports}
            className="shrink-0 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 text-[11px] font-semibold transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="py-16 text-center text-slate-500">
          <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin text-indigo-400" />
          <p className="text-xs">Computing analytics from database records...</p>
        </div>
      ) : errorMsg ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900 border border-rose-500/20">
          <AlertTriangle className="w-10 h-10 text-rose-400/70 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-white">Could not compute operational reports</h4>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">{errorMsg}</p>
        </div>
      ) : reportData ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
            <span className="text-xs text-slate-400 font-medium block">Total Registered Shipments</span>
            <div className="text-3xl font-bold text-white">{reportData.totalShipments}</div>
            <p className="text-[11px] text-slate-500">Recorded in primary PostgreSQL store</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
            <span className="text-xs text-slate-400 font-medium block">Delivered Orders</span>
            <div className="text-3xl font-bold text-emerald-400">{reportData.delivered}</div>
            <p className="text-[11px] text-slate-500">Successfully completed consignments</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
            <span className="text-xs text-slate-400 font-medium block">On-Time Delivery Rate</span>
            <div className="text-3xl font-bold text-indigo-400">{reportData.onTimeDeliveryRate}%</div>
            <p className="text-[11px] text-slate-500">Calculated delivery accuracy</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
            <span className="text-xs text-slate-400 font-medium block">Active Drivers On Dispatch</span>
            <div className="text-3xl font-bold text-violet-400">{reportData.activeDrivers}</div>
            <p className="text-[11px] text-slate-500">Fleet drivers actively handling orders</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
