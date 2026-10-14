"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Compass, AlertCircle, Loader2, CheckCircle2, ArrowLeft } from "lucide-react";
import { apiClient } from "@/lib/api-client";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError("Missing or invalid password reset token. Please request a new link.");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("New password and confirm password do not match.");
      return;
    }

    setIsLoading(true);

    try {
      const res = await apiClient.customerResetPassword({
        token,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });

      if (res && res.success) {
        setIsSuccess(true);
      } else {
        throw new Error(res?.message || "Password reset failed. Please try again.");
      }
    } catch (err: any) {
      setError(err?.message || "Invalid or expired password reset link.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!token && !isSuccess) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-7 sm:p-8 max-w-[430px] w-full text-center space-y-4">
        <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Invalid Reset Link</h2>
        <p className="text-xs text-slate-400">
          No password reset token was provided in the link. Please request a new reset link.
        </p>
        <Link
          href="/forgot-password"
          className="inline-flex items-center justify-center w-full h-12 px-4 bg-sky-500 hover:bg-sky-400 text-white font-medium rounded-xl transition-all text-xs sm:text-sm"
        >
          Request Reset Link
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-7 sm:p-8 max-w-[430px] w-full font-sans">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-500 to-blue-600 shadow-lg shadow-sky-500/25 mb-3">
          <Compass className="w-7 h-7 text-white" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white leading-tight">Travelogix</h1>
        <h2 className="text-xs sm:text-sm font-semibold text-sky-400 mt-1">Set New Password</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Enter your new password below
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {isSuccess ? (
        <div className="space-y-4 text-center">
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-start space-x-2.5 leading-relaxed text-left">
            <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400 mt-0.5" />
            <div>
              <p className="font-semibold text-emerald-200 mb-1">Password Reset Successful!</p>
              <p>Your password has been updated. You can now sign in with your new credentials.</p>
            </div>
          </div>
          <Link
            href="/login"
            className="w-full h-12 px-4 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-medium rounded-xl transition-all text-xs sm:text-sm flex items-center justify-center space-x-2 shadow-lg shadow-sky-500/20"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Login</span>
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label htmlFor="newPassword" className="block text-xs font-medium text-slate-300 mb-1 uppercase tracking-wider">
              New Password
            </label>
            <input
              id="newPassword"
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="At least 8 characters"
              className="w-full h-12 px-4 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500 text-xs sm:text-sm"
            />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-xs font-medium text-slate-300 mb-1 uppercase tracking-wider">
              Confirm New Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              required
              minLength={8}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter new password"
              className="w-full h-12 px-4 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500 text-xs sm:text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || !newPassword || !confirmPassword}
            className="w-full h-12 mt-1 px-4 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-medium rounded-xl shadow-lg shadow-sky-500/20 transition-all focus:outline-none focus:ring-2 focus:ring-sky-400 disabled:opacity-50 text-xs sm:text-sm flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Updating Password...</span>
              </>
            ) : (
              <span>Reset Password</span>
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

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-7 max-w-[430px] w-full text-center space-y-3 shadow-2xl">
        <Loader2 className="w-6 h-6 animate-spin text-sky-400 mx-auto" />
        <p className="text-xs text-slate-400">Loading password reset form...</p>
      </div>
    }>
      <ResetPasswordForm />
    </Suspense>
  );
}
