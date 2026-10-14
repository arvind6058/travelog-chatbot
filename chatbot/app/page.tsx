import React from "react";
import Link from "next/link";
import { ADMIN_LOGIN_URL } from "@/lib/env";
import {
  Compass,
  Sparkles,
  ArrowRight,
  Plane,
  Hotel,
  Train,
  Bus,
  Package,
  Search,
  MessageSquare
} from "lucide-react";

export default function CustomerHomePage() {
  const quickActions = [
    { label: "Plan a Trip", href: "/ai-assistant?intent=travel", icon: Plane },
    { label: "Find a Hotel", href: "/ai-assistant?intent=hotel", icon: Hotel },
    { label: "Find a Train", href: "/ai-assistant?intent=train", icon: Train },
    { label: "Find a Bus", href: "/ai-assistant?intent=bus", icon: Bus },
    { label: "Track Shipment", href: "/ai-assistant?intent=tracking", icon: Package },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-sky-500 selection:text-white relative overflow-hidden">
      {/* Background ambient lighting effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-tr from-sky-600/15 via-blue-600/10 to-indigo-600/15 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center shadow-lg shadow-sky-500/25 group-hover:scale-105 transition-transform">
              <Compass className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white block leading-tight">Travelogix</span>
              <span className="block text-[10px] text-sky-400 font-medium uppercase tracking-wider">AI Assistant</span>
            </div>
          </Link>

          <div className="flex items-center space-x-3">
            <Link
              href="/login"
              className="text-xs sm:text-sm font-medium text-slate-300 hover:text-white px-3.5 py-2 rounded-xl hover:bg-slate-800/80 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="text-xs sm:text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 px-4 py-2 rounded-xl transition-all"
            >
              Register
            </Link>
          </div>
        </div>
      </header>

      {/* Chatbot-Style Entry Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-12 sm:py-16 text-center max-w-3xl mx-auto w-full relative z-10">
        
        {/* AI Sparkle Icon / Badge */}
        <div className="mb-6 flex items-center justify-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-sky-500/20 via-blue-500/10 to-indigo-500/20 border border-sky-500/30 flex items-center justify-center shadow-xl shadow-sky-500/10 backdrop-blur-sm">
            <Sparkles className="w-8 h-8 text-sky-400 animate-pulse" />
          </div>
        </div>

        {/* Branding & Subtitle */}
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-2">
          Travelogix AI Assistant
        </h1>
        <p className="text-lg sm:text-xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-400 mb-3">
          Travel &amp; Logistics in One Chat
        </p>
        <p className="text-sm sm:text-base text-slate-400 max-w-lg mb-10 leading-relaxed font-normal">
          Plan trips, explore travel options, and manage logistics with AI.
        </p>

        {/* Visual Chat Prompt Container */}
        <Link
          href="/ai-assistant"
          className="w-full max-w-2xl bg-slate-900/80 border border-slate-800 hover:border-sky-500/50 rounded-2xl p-4 sm:p-5 shadow-2xl backdrop-blur-md transition-all group mb-8 text-left block"
        >
          <div className="flex items-center justify-between text-slate-400 group-hover:text-slate-200 transition-colors">
            <div className="flex items-center space-x-3">
              <Search className="w-5 h-5 text-sky-400" />
              <span className="text-sm sm:text-base font-medium text-slate-300">
                What can I help you with?
              </span>
            </div>
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-semibold">
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Ask AI</span>
            </div>
          </div>
        </Link>

        {/* Quick Actions Bar */}
        <div className="w-full max-w-2xl mb-10">
          <p className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-3 text-center sm:text-left">
            Suggested Quick Actions
          </p>
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2.5">
            {quickActions.map((action) => {
              const ActionIcon = action.icon;
              return (
                <Link
                  key={action.label}
                  href={action.href}
                  className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-sky-500/40 hover:bg-slate-800/80 text-xs font-medium text-slate-300 hover:text-white transition-all shadow-sm"
                >
                  <ActionIcon className="w-3.5 h-3.5 text-sky-400" />
                  <span>{action.label}</span>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Primary Action Button */}
        <div>
          <Link
            href="/ai-assistant"
            className="inline-flex items-center justify-center space-x-2.5 px-8 py-4 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-semibold text-base shadow-xl shadow-sky-500/25 hover:shadow-sky-500/40 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <span>Start AI Assistant</span>
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-5 text-center text-xs text-slate-500 relative z-10">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p>Travelogix AI Assistant &bull; Integrated Travel &amp; Logistics Platform</p>
          <a
            href={ADMIN_LOGIN_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-slate-500 hover:text-slate-300 transition-colors underline decoration-slate-700"
          >
            Admin Portal
          </a>
        </div>
      </footer>
    </div>
  );
}

