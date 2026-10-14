"use client";

import React from "react";
import { Clock, MapPin, CheckCircle2 } from "lucide-react";

export interface TimelineItem {
  id: string;
  title: string;
  description?: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  timestamp?: string;
  isLatest?: boolean;
}

interface TrackingTimelineProps {
  items: TimelineItem[];
  emptyMessage?: string;
}

export const TrackingTimeline: React.FC<TrackingTimelineProps> = ({
  items,
  emptyMessage = "No historical tracking events recorded.",
}) => {
  if (!items || items.length === 0) {
    return (
      <div className="py-6 text-center text-slate-500 italic text-xs">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="relative pl-5 space-y-4 border-l border-slate-800">
      {items.map((item, idx) => {
        const isLatest = idx === 0 || item.isLatest;
        return (
          <div key={item.id || idx} className="relative group">
            {/* Timeline Circle Bullet */}
            <div
              className={`absolute -left-[25px] top-1 w-3 h-3 rounded-full border-2 transition-all ${
                isLatest
                  ? "bg-indigo-500 border-indigo-300 ring-4 ring-indigo-500/20"
                  : "bg-slate-800 border-slate-700 group-hover:border-indigo-400"
              }`}
            />

            <div className="text-xs space-y-1">
              <div className="flex items-center justify-between font-semibold">
                <span className={isLatest ? "text-white font-bold" : "text-slate-300"}>
                  {item.title}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {item.timestamp ? new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                </span>
              </div>

              {item.description && (
                <p className="text-slate-400 text-[11px] leading-relaxed">{item.description}</p>
              )}

              {item.location && (
                <div className="flex items-center space-x-1 text-[10px] text-slate-400">
                  <MapPin className="w-3 h-3 text-indigo-400 shrink-0" />
                  <span className="font-mono">{item.location}</span>
                </div>
              )}

              {typeof item.latitude === "number" && typeof item.longitude === "number" && (
                <div className="text-[10px] text-slate-500 font-mono pl-4">
                  GPS: {item.latitude.toFixed(4)}, {item.longitude.toFixed(4)}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
