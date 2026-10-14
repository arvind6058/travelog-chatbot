"use client";

import React, { useState, useEffect } from "react";
import { ShieldCheck, Lock, AlertCircle } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";

export default function AdminLoginPage() {
  // Never pre-fill real credentials: the previous defaults shipped the seeded
  // administrator password to every visitor of this page.
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextParam, setNextParam] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const next = params.get("next");
      // Validate relative path to prevent open redirect vulnerabilities
      if (next && next.startsWith("/admin/") && !next.startsWith("//")) {
        setNextParam(next);
      }
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // The backend sets the httpOnly `travelogix_admin_token` cookie on this
      // response; nothing is stored in localStorage and no cookie is written
      // from JavaScript.
      const data = await adminApiClient.post<any>("/auth/admin/login", { email, password });

      if (data && data.success === false) {
        throw new Error(data.detail || data.message || "Invalid administrative credentials.");
      }

      // Secure Navigation after login
      const targetPath = nextParam || "/admin/dashboard";
      window.location.href = targetPath;
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please verify credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8 max-w-md w-full">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/25 mb-4">
          <ShieldCheck className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Travelogix Admin</h1>
        <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
          Internal Operations Console
        </p>
      </div>

      {error && (
        <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {nextParam && (
        <div className="mb-4 p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs">
          Sign in required to access: <code className="font-mono text-white">{nextParam}</code>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="adminId" className="block text-xs font-medium text-slate-300 mb-1.5 uppercase tracking-wider">
            Admin ID / Email
          </label>
          <input
            id="adminId"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@travelogix.internal"
            className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label htmlFor="adminPassword" className="block text-xs font-medium text-slate-300 uppercase tracking-wider">
              Password
            </label>
            <a href="#forgot" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
              Forgot Password?
            </a>
          </div>
          <input
            id="adminPassword"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/20 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50 text-sm flex items-center justify-center space-x-2"
        >
          <Lock className="w-4 h-4" />
          <span>{isLoading ? "Authenticating..." : "Login"}</span>
        </button>
      </form>

      <div className="mt-8 pt-4 border-t border-slate-800/80 text-center">
        <p className="text-[11px] text-slate-500">
          Restricted access. All administrative actions are recorded in immutable audit logs.
        </p>
      </div>
    </div>
  );
}
