"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Compass, AlertCircle, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { GOOGLE_OAUTH_LOGIN_URL } from "@/lib/env";

export default function CustomerLoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextParam, setNextParam] = useState<string>("/ai-assistant");
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const next = params.get("next");
      const errParam = params.get("error");

      if (errParam === "google_login_failed") {
        setError("Google sign-in could not be completed. Please ensure you completed Google consent.");
      } else if (errParam === "google_oauth_not_configured") {
        setError("Google OAuth client is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env.");
      } else if (errParam === "google_secret_invalid") {
        setError("Google Client Secret is missing or invalid. Please set your real GOOGLE_CLIENT_SECRET in backend/.env.");
      }

      if (next && next.startsWith("/") && !next.startsWith("//")) {
        setNextParam(next);
      }

      // Check if user is already authenticated
      apiClient.getCustomerMe()
        .then((res) => {
          if (res && res.authenticated) {
            const target = next && next.startsWith("/") ? next : "/ai-assistant";
            window.location.href = target;
          } else {
            setCheckingAuth(false);
          }
        })
        .catch(() => {
          setCheckingAuth(false);
        });
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await apiClient.customerLogin(email, password);
      if (response && response.success) {
        window.location.href = nextParam;
      } else {
        throw new Error(response?.message || "Email or password is incorrect.");
      }
    } catch (err: any) {
      setError(err.message || "Email or password is incorrect.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = GOOGLE_OAUTH_LOGIN_URL;
  };

  if (checkingAuth) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-7 max-w-[430px] w-full text-center space-y-3 shadow-2xl">
        <Loader2 className="w-6 h-6 animate-spin text-sky-400 mx-auto" />
        <p className="text-xs text-slate-400">Checking customer session...</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-7 sm:p-8 max-w-[430px] w-full">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-500 to-blue-600 shadow-lg shadow-sky-500/25 mb-3">
          <Compass className="w-7 h-7 text-white" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white leading-tight">Travelogix</h1>
        <h2 className="text-xs sm:text-sm font-semibold text-sky-400 mt-1">Welcome to Travelogix</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Sign in to access your customer AI assistant
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Email / Password Form */}
      <form onSubmit={handleSubmit} className="space-y-3.5">
        <div>
          <label htmlFor="email" className="block text-xs font-medium text-slate-300 mb-1 uppercase tracking-wider">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full h-12 px-4 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500 text-xs sm:text-sm"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label htmlFor="password" className="block text-xs font-medium text-slate-300 uppercase tracking-wider">
              Password
            </label>
            <Link href="/forgot-password" className="text-xs text-sky-400 hover:text-sky-300 transition-colors">
              Forgot Password?
            </Link>
          </div>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full h-12 px-4 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500 text-xs sm:text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full h-12 mt-1 px-4 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-medium rounded-xl shadow-lg shadow-sky-500/20 transition-all focus:outline-none focus:ring-2 focus:ring-sky-400 disabled:opacity-50 text-xs sm:text-sm flex items-center justify-center space-x-2"
        >
          <span>{isLoading ? "Signing in..." : "Continue"}</span>
        </button>
      </form>

      {/* Divider */}
      <div className="relative my-5">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-800" />
        </div>
        <div className="relative flex justify-center text-[11px] uppercase">
          <span className="bg-slate-900 px-3 text-slate-500 font-medium tracking-wider">OR</span>
        </div>
      </div>

      {/* Real Google OAuth Login Button */}
      <button
        type="button"
        onClick={handleGoogleLogin}
        disabled={isLoading}
        className="w-full h-12 px-4 bg-slate-950 hover:bg-slate-800 border border-slate-700 text-slate-200 font-medium rounded-xl transition-all flex items-center justify-center space-x-3 text-xs sm:text-sm disabled:opacity-50"
      >
        <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
          />
        </svg>
        <span>Continue with Google</span>
      </button>

      {/* Footer link to Register */}
      <div className="mt-6 pt-5 border-t border-slate-800 text-center">
        <Link
          href="/register"
          className="text-xs font-medium text-sky-400 hover:text-sky-300 transition-colors"
        >
          Create New Account
        </Link>
      </div>
    </div>
  );
}
