import React from "react";
import { Bus } from "lucide-react";

export default function BusesPage() {
  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Bus className="w-6 h-6 text-sky-400" />
          <span>Intercity Bus Routes & Live ETA</span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">Search intercity bus operators, routes, and verified arrival schedules</p>
      </div>
      <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
        <p className="text-sm text-slate-400">Intercity bus routes and ETA interface ready for Phase 8 integration.</p>
      </div>
    </div>
  );
}
