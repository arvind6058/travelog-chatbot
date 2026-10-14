"use client";

import React from "react";
import { Radio, ShieldCheck, Database, Zap } from "lucide-react";

interface RealtimeIndicatorProps {
  isConnected: boolean;
  isMock?: boolean;
  mode?: string;
  source?: string;
}

export const RealtimeIndicator: React.FC<RealtimeIndicatorProps> = ({
  isConnected,
  isMock = false,
  mode = "live",
  source = "travelogix_postgresql_db",
}) => {
  // Determine mode badge text & styling according to rules:
  // LIVE only when real live data exists (isMock: false, mode: live)
  // DEMO DATA when seeded/demo records (isMock: true)
  // DEMO SIMULATION for test streams
  let modeLabel = "LIVE";
  let modeBadgeStyle = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";

  if (mode === "simulation" || mode === "test") {
    modeLabel = "DEMO SIMULATION";
    modeBadgeStyle = "bg-purple-500/10 text-purple-400 border-purple-500/30";
  } else if (isMock || mode === "demo") {
    modeLabel = "DEMO DATA";
    modeBadgeStyle = "bg-amber-500/10 text-amber-400 border-amber-500/30";
  }

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      {/* Realtime Socket Connection Status */}
      <div
        className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full border transition-all ${
          isConnected
            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
            : "bg-rose-500/10 text-rose-400 border-rose-500/30"
        }`}
        title={isConnected ? "Realtime WebSocket channel active" : "Realtime channel disconnected"}
      >
        <Radio className={`w-3.5 h-3.5 ${isConnected ? "animate-pulse text-emerald-400" : ""}`} />
        <span className="font-semibold tracking-wide text-[11px]">
          {isConnected ? "Connected" : "Disconnected"}
        </span>
      </div>

      {/* Verified Data Source Mode */}
      <div className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full border font-bold text-[11px] ${modeBadgeStyle}`}>
        <Zap className="w-3.5 h-3.5" />
        <span>{modeLabel}</span>
      </div>

      {/* DB Persistence Verification Badge */}
      <div className="hidden md:flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-900 text-slate-400 border border-slate-800 text-[11px]">
        <Database className="w-3.5 h-3.5 text-indigo-400" />
        <span>PostgreSQL Persistent</span>
      </div>
    </div>
  );
};
