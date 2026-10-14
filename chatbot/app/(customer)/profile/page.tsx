"use client";

import React, { useEffect, useState } from "react";
import { User, Shield, Mail, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";

type CustomerProfile = {
  id?: string;
  email?: string;
  name?: string;
  role?: string;
};

export default function CustomerProfilePage() {
  // The page used to render literal placeholders ("India (Default Context)",
  // "CUSTOMER") and never displayed the signed-in account at all.
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const res = await apiClient.getCustomerMe();
        if (cancelled) return;
        if (res && res.authenticated && res.user) {
          setProfile(res.user);
        } else {
          setError("Your session has expired. Please sign in again.");
        }
      } catch {
        if (!cancelled) setError("Could not load your profile right now.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="max-w-4xl mx-auto w-full px-4 py-8 space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight">Customer Profile</h1>
        <p className="text-sm text-slate-400 mt-1">Manage your Travelogix account and regional preferences</p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center space-x-4">
          <div className="w-14 h-14 rounded-2xl bg-sky-500/10 text-sky-400 flex items-center justify-center border border-sky-500/20">
            <User className="w-7 h-7" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">
              {isLoading ? "Loading account…" : profile?.name || "Customer Account"}
            </h3>
            <p className="text-xs text-slate-400">
              {profile?.email || "Authenticated via Customer Session"}
            </p>
          </div>
        </div>

        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-slate-400 pt-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading your account details…
          </div>
        )}

        {error && !isLoading && (
          <p className="text-xs text-rose-400 pt-2">{error}</p>
        )}

        {profile && !isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-800 text-sm">
            <div>
              <span className="text-xs text-slate-500 uppercase tracking-wider block">Email</span>
              <span className="text-slate-200 font-medium inline-flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-slate-500" />
                {profile.email}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-500 uppercase tracking-wider block">Role</span>
              <span className="text-slate-200 font-medium inline-flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-slate-500" />
                {profile.role || "CUSTOMER"}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-500 uppercase tracking-wider block">Account ID</span>
              <span className="text-slate-200 font-medium font-mono text-xs">
                {profile.id ? `${profile.id.slice(0, 8)}…` : "—"}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-500 uppercase tracking-wider block">Regional Focus</span>
              <span className="text-slate-200 font-medium">India</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
