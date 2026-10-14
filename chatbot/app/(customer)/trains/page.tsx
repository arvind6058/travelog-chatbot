import React from "react";
import { Train } from "lucide-react";

export default function TrainsPage() {
  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Train className="w-6 h-6 text-sky-400" />
          <span>Train Schedules & Live Status</span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">Indian Railways live train running status, PNR verification, and coach schedules</p>
      </div>
      <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
        <p className="text-sm text-slate-400">Train schedules and live status tracking interface ready for Phase 8 integration.</p>
      </div>
    </div>
  );
}
