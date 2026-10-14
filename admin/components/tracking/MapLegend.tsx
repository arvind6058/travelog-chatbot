"use client";

import React from "react";

export const MapLegend: React.FC = () => {
  return (
    <div className="absolute bottom-4 left-4 z-10 px-3.5 py-2.5 rounded-xl bg-slate-950/90 border border-slate-800 backdrop-blur-md shadow-xl text-xs space-y-1.5 select-none">
      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Map Legend</div>
      
      <div className="flex items-center space-x-2">
        <div className="w-5 h-5 rounded-full bg-indigo-600 flex items-center justify-center text-[10px] text-white font-bold border border-white/40">
          📦
        </div>
        <span className="text-slate-200 font-medium text-[11px]">Shipment Location</span>
      </div>

      <div className="flex items-center space-x-2">
        <div className="w-5 h-5 rounded-full bg-purple-600 flex items-center justify-center text-[10px] text-white font-bold border border-white/40">
          🚚
        </div>
        <span className="text-slate-200 font-medium text-[11px]">Driver Location</span>
      </div>

      <div className="flex items-center space-x-2">
        <div className="w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center text-[10px] text-white font-bold border border-white/40">
          🟢
        </div>
        <span className="text-slate-200 font-medium text-[11px]">Origin</span>
      </div>

      <div className="flex items-center space-x-2">
        <div className="w-5 h-5 rounded-full bg-rose-500 flex items-center justify-center text-[10px] text-white font-bold border border-white/40">
          🔴
        </div>
        <span className="text-slate-200 font-medium text-[11px]">Destination</span>
      </div>

      <div className="flex items-center space-x-2 pt-0.5">
        <div className="w-5 h-0 border-b-2 border-dashed border-indigo-400"></div>
        <span className="text-slate-400 text-[11px]">Active Route</span>
      </div>
    </div>
  );
};
