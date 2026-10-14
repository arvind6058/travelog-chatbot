"use client";

import React, { useState, useEffect } from "react";
import { UserCheck, Loader2, RefreshCw, Mail, Phone } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";

export default function AdminCustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchCustomers = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminApiClient.get<any>("/admin/customers");
      if (res && res.success) {
        setCustomers(res.customers || []);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to fetch customers from backend.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <UserCheck className="w-6 h-6 text-indigo-400" />
            <span>Customer Directory</span>
            {isLoading && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Registered customer accounts, contact details, and consignment histories persisted in PostgreSQL.
          </p>
        </div>

        <button
          onClick={fetchCustomers}
          disabled={isLoading}
          className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
          title="Refresh List"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {errorMsg}
        </div>
      )}

      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center text-slate-500">
            <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin text-indigo-400" />
            <p className="text-xs">Fetching customers from PostgreSQL database...</p>
          </div>
        ) : customers.length === 0 ? (
          <div className="p-12 text-center">
            <UserCheck className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h4 className="text-sm font-semibold text-white">No registered customers</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Customer accounts created via registration will be listed here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th scope="col" className="p-3 font-semibold">Customer ID</th>
                  <th scope="col" className="p-3 font-semibold">Full Name</th>
                  <th scope="col" className="p-3 font-semibold">Email</th>
                  <th scope="col" className="p-3 font-semibold">Phone</th>
                  <th scope="col" className="p-3 font-semibold">Registered At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {customers.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 font-mono text-indigo-400 font-bold">{c.id.slice(0, 8)}...</td>
                    <td className="p-3 font-medium text-white">{c.full_name}</td>
                    <td className="p-3 text-slate-300">
                      <div className="flex items-center space-x-1.5">
                        <Mail className="w-3 h-3 text-slate-500" />
                        <span>{c.email}</span>
                      </div>
                    </td>
                    <td className="p-3 text-slate-300">
                      <div className="flex items-center space-x-1.5">
                        <Phone className="w-3 h-3 text-slate-500" />
                        <span>{c.phone || "N/A"}</span>
                      </div>
                    </td>
                    <td className="p-3 text-slate-500">
                      {c.created_at ? new Date(c.created_at).toLocaleDateString() : "N/A"}
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
