"use client";

import React, { useState, useEffect } from "react";
import { CheckCircle, Loader2, RefreshCw, AlertTriangle } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";

export default function DeliveredShipmentsPage() {
  const [delivered, setDelivered] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchDelivered = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminApiClient.get<any>("/admin/delivered");
      if (res && res.success) {
        setDelivered(res.shipments || []);
      }
    } catch (e: any) {
      // A failed fetch must not render as "no completed shipments yet".
      setErrorMsg(e?.message || "Failed to fetch delivered shipments from backend.");
      setDelivered([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDelivered();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-emerald-400" />
            <span>Delivered Consignments</span>
            {isLoading && <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />}
          </h1>
          <p className="text-xs text-slate-400 mt-1">Archive of successfully delivered shipments persisted in PostgreSQL</p>
        </div>

        <button
          onClick={fetchDelivered}
          disabled={isLoading}
          className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
          title="Refresh List"
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
            onClick={fetchDelivered}
            className="shrink-0 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 text-[11px] font-semibold transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center text-slate-500">
            <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin text-emerald-400" />
            <p className="text-xs">Fetching delivered consignments from database...</p>
          </div>
        ) : errorMsg ? (
          <div className="p-12 text-center">
            <AlertTriangle className="w-10 h-10 text-rose-400/70 mx-auto mb-3" />
            <p className="text-sm font-semibold text-white">Could not load delivered consignments</p>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">{errorMsg}</p>
          </div>
        ) : delivered.length === 0 ? (
          <div className="p-12 text-center">
            <CheckCircle className="w-10 h-10 text-slate-600 mx-auto mb-3 opacity-40" />
            <p className="text-sm font-semibold text-slate-300">No completed delivered shipments yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th scope="col" className="p-3 font-semibold">Tracking ID</th>
                  <th scope="col" className="p-3 font-semibold">Customer</th>
                  <th scope="col" className="p-3 font-semibold">Route</th>
                  <th scope="col" className="p-3 font-semibold">Cost (â‚¹)</th>
                  <th scope="col" className="p-3 font-semibold">Delivery Date</th>
                  <th scope="col" className="p-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {delivered.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 font-mono text-emerald-400 font-bold">{s.tracking_id}</td>
                    <td className="p-3 font-medium text-white">{s.customer_name}</td>
                    <td className="p-3 text-slate-300">{s.origin} &rarr; {s.destination}</td>
                    <td className="p-3 font-semibold text-white">â‚¹{s.cost_inr}</td>
                    <td className="p-3 text-emerald-300 font-medium">{s.actual_delivery_date || s.expected_delivery_date}</td>
                    <td className="p-3">
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {s.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
