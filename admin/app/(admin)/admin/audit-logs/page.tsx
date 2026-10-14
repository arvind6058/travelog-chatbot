"use client";

import React, { useState, useEffect } from "react";
import { ShieldAlert, ShieldCheck, Loader2, RefreshCw, AlertTriangle } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";

export default function AdminAuditLogsPage() {
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchAuditLogs = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminApiClient.get<any>("/admin/audit-logs");
      if (res && res.success) {
        setAuditLogs(res.audit_logs || []);
      }
    } catch (e: any) {
      // A failed fetch must not render as "no audit records logged yet".
      setErrorMsg(e?.message || "Failed to fetch audit logs from backend.");
      setAuditLogs([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-indigo-400" />
            <span>Security & Operational Audit Logs</span>
            {isLoading && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Immutable event log of administrative actions, assignments, driver KYC changes, and security events persisted in PostgreSQL.
          </p>
        </div>

        <button
          onClick={fetchAuditLogs}
          disabled={isLoading}
          className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
          title="Refresh Logs"
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
            onClick={fetchAuditLogs}
            className="shrink-0 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 text-[11px] font-semibold transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center text-slate-500">
            <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin text-indigo-400" />
            <p className="text-xs">Fetching audit trail from PostgreSQL database...</p>
          </div>
        ) : errorMsg ? (
          <div className="p-12 text-center">
            <AlertTriangle className="w-10 h-10 text-rose-400/70 mx-auto mb-3" />
            <h4 className="text-sm font-semibold text-white">Could not load audit records</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">{errorMsg}</p>
          </div>
        ) : auditLogs.length === 0 ? (
          <div className="p-12 text-center">
            <ShieldCheck className="w-10 h-10 text-slate-600 mx-auto mb-3 opacity-40" />
            <h4 className="text-sm font-semibold text-white">No audit records logged yet</h4>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th scope="col" className="p-3 font-semibold">Action</th>
                  <th scope="col" className="p-3 font-semibold">Actor</th>
                  <th scope="col" className="p-3 font-semibold">Entity Type & ID</th>
                  <th scope="col" className="p-3 font-semibold">Description</th>
                  <th scope="col" className="p-3 font-semibold">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {auditLogs.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        {l.action}
                      </span>
                    </td>
                    <td className="p-3 font-medium text-slate-200">{l.actor}</td>
                    <td className="p-3 text-slate-300">
                      <span className="text-slate-400">{l.entity_type}:</span> <span className="font-mono text-indigo-300">{l.entity_id}</span>
                    </td>
                    <td className="p-3 text-slate-300 max-w-md truncate">{l.description}</td>
                    <td className="p-3 text-slate-500">
                      {l.timestamp ? new Date(l.timestamp).toLocaleString() : ""}
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
