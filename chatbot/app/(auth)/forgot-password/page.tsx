"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Compass, AlertCircle, Loader2, CheckCircle2, ArrowLeft } from "lucide-react";
import { apiClient } from "@/lib/api-client";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setIsLoading(true);

    try {
      const res = await apiClient.customerForgotPassword(email);
      setSuccessMsg(res?.message || "If an account exists for this email, a password reset link has been sent.");
    } catch (err: any) {
      setError(err?.message || "Failed to request password reset link. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-7 sm:p-8 max-w-[430px] w-full font-sans">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-500 to-blue-600 shadow-lg shadow-sky-500/25 mb-3">
          <Compass className="w-7 h-7 text-white" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white leading-tight">Travelogix</h1>
        <h2 className="text-xs sm:text-sm font-semibold text-sky-400 mt-1">Forgot Password?</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Enter your email address to receive a password reset link
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {successMsg ? (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-start space-x-2.5 leading-relaxed">
            <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400 mt-0.5" />
            <div>
              <p className="font-semibold text-emerald-200 mb-1">Check Your Email</p>
              <p>{successMsg}</p>
            </div>
          </div>
          <Link
            href="/login"
            className="w-full h-12 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium rounded-xl transition-all text-xs sm:text-sm flex items-center justify-center space-x-2 border border-slate-700"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Login</span>
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-xs font-medium text-slate-300 mb-1 uppercase tracking-wider">
              Email Address
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

          <button
            type="submit"
            disabled={isLoading || !email.trim()}
            className="w-full h-12 px-4 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-medium rounded-xl shadow-lg shadow-sky-500/20 transition-all focus:outline-none focus:ring-2 focus:ring-sky-400 disabled:opacity-50 text-xs sm:text-sm flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Sending Link...</span>
              </>
            ) : (
              <span>Send Reset Link</span>
            )}
          </button>

          <div className="pt-3 border-t border-slate-800 text-center">
            <Link
              href="/login"
              className="inline-flex items-center space-x-1.5 text-xs font-medium text-sky-400 hover:text-sky-300 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Login</span>
            </Link>
          </div>
        </form>
      )}
    </div>
  );
}
