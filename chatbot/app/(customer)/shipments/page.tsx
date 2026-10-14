"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Package, PlusCircle, RefreshCw, Loader2, Truck, ArrowRight } from "lucide-react";
import { apiClient } from "@/lib/api-client";

export default function MyShipmentsPage() {
  const [shipments, setShipments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchShipments = async (signal?: AbortSignal) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      // The backend scopes this list from the signed-in session cookie; the
      // old `?email=` query parameter was client-controlled and has been
      // removed from the API entirely.
      const res = await apiClient.get<any>("/shipments");
      if (signal?.aborted) return;
      if (res && res.success) {
        setShipments(res.shipments || []);
      } else {
        setErrorMsg("The backend did not return a shipment list.");
      }
    } catch (err: any) {
      if (signal?.aborted) return;
      setErrorMsg(err.message || "Failed to load shipments.");
    } finally {
      if (!signal?.aborted) setIsLoading(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    fetchShipments(controller.signal);
    return () => controller.abort();
  }, []);

  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>My Shipments</span>
            {isLoading && <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />}
          </h1>
          <p className="text-xs text-slate-400 mt-1">Review active and historical consignments persisted in PostgreSQL</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => fetchShipments()}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
            title="Refresh List"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-sky-400" : ""}`} />
          </button>
          <Link
            href="/logistics/register"
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-medium text-xs shadow-md shadow-sky-500/20 transition-all"
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

      {isLoading ? (
        <div className="py-16 text-center text-slate-500 border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
          <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin text-sky-400" />
          <p className="text-xs">Fetching registered shipments from backend database...</p>
        </div>
      ) : errorMsg ? (
        <div className="p-12 text-center border border-rose-500/20 rounded-2xl bg-rose-500/5">
          <Package className="w-10 h-10 text-rose-400/70 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-white">Could not load your shipments</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">{errorMsg}</p>
          <button
            onClick={() => fetchShipments()}
            className="mt-4 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 text-xs font-semibold transition-colors"
          >
            Retry
          </button>
        </div>
      ) : shipments.length === 0 ? (
        <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
          <Package className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-white">No active shipments found</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            You haven&apos;t registered any consignments yet. Click &quot;+ Register New Shipment&quot; to register your first package.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {shipments.map((s) => (
            <div key={s.id} className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 space-y-4 transition-all">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm text-sky-400 font-bold">{s.tracking_id}</span>
                <span className="px-2.5 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 text-[10px] font-semibold uppercase">
                  {s.status}
                </span>
              </div>

              <div className="space-y-1 text-xs">
                <div className="text-slate-200 font-medium">{s.package_name} ({s.weight_kg} kg)</div>
                <div className="text-slate-400 flex items-center justify-between pt-1">
                  <span>{s.origin} &rarr; {s.destination}</span>
                  <span className="font-semibold text-white">₹{s.cost_inr}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                <div><span className="text-slate-500">Shipper:</span> {s.shipper_name}</div>
                <div><span className="text-slate-500">Recipient:</span> {s.recipient_name}</div>
                <div><span className="text-slate-500">Pickup:</span> {s.pickup_date || "N/A"}</div>
                <div><span className="text-slate-500">Expected:</span> {s.expected_delivery_date || "N/A"}</div>
              </div>

              <div className="pt-2">
                <Link
                  href={`/logistics?track=${s.tracking_id}`}
                  className="w-full py-2 rounded-xl bg-slate-950 hover:bg-slate-800 text-sky-400 border border-slate-800 text-xs font-semibold flex items-center justify-center space-x-1 transition-colors"
                >
                  <Truck className="w-3.5 h-3.5" />
                  <span>Track Consignment</span>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
