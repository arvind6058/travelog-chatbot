"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Compass, AlertCircle, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";

export default function CustomerRegisterPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    if (typeof window !== "undefined") {
      apiClient.getCustomerMe()
        .then((res) => {
          if (res && res.authenticated) {
            window.location.href = "/ai-assistant";
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

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiClient.customerRegister({
        email,
        password,
        full_name: fullName,
        phone,
      });

      if (response && response.success) {
        window.location.href = "/ai-assistant";
      } else {
        throw new Error(response?.message || "Registration failed.");
      }
    } catch (err: any) {
      setError(err.message || "Registration failed. Please check input details.");
    } finally {
      setIsLoading(false);
    }
  };

  if (checkingAuth) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-md w-full text-center space-y-3">
        <Loader2 className="w-6 h-6 animate-spin text-sky-400 mx-auto" />
        <p className="text-xs text-slate-400">Checking customer session...</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8 max-w-md w-full">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-500 to-blue-600 shadow-lg shadow-sky-500/25 mb-3">
          <Compass className="w-7 h-7 text-white" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-white">Travelogix</h1>
        <h2 className="text-sm font-semibold text-sky-400 mt-1">Create your account</h2>
      </div>

      {error && (
        <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-3.5">
        <div>
          <label htmlFor="fullName" className="block text-xs font-medium text-slate-300 mb-1 uppercase tracking-wider">
            Full Name
          </label>
          <input
            id="fullName"
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="John Doe"
            className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm"
          />
        </div>

        <div>
          <label htmlFor="regEmail" className="block text-xs font-medium text-slate-300 mb-1 uppercase tracking-wider">
            Email
          </label>
          <input
            id="regEmail"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm"
          />
        </div>

        <div>
          <label htmlFor="phone" className="block text-xs font-medium text-slate-300 mb-1 uppercase tracking-wider">
            Phone Number
          </label>
          <input
            id="phone"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+1 555-0199"
            className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm"
          />
        </div>

        <div>
          <label htmlFor="regPassword" className="block text-xs font-medium text-slate-300 mb-1 uppercase tracking-wider">
            Password
          </label>
          <input
            id="regPassword"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm"
          />
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-xs font-medium text-slate-300 mb-1 uppercase tracking-wider">
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            type="password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full mt-3 py-2.5 px-4 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-medium rounded-xl shadow-lg shadow-sky-500/20 transition-all focus:outline-none focus:ring-2 focus:ring-sky-400 disabled:opacity-50 text-sm"
        >
          {isLoading ? "Creating Account..." : "Create Account"}
        </button>
      </form>

      <div className="mt-6 pt-5 border-t border-slate-800 text-center">
        <Link
          href="/login"
          className="text-xs font-medium text-sky-400 hover:text-sky-300 transition-colors"
        >
          Already have an account? Sign In
        </Link>
      </div>
    </div>
  );
}
