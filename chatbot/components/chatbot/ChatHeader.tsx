"use client";

import React from "react";
import { Compass, Plane, Package, Minus, X, PlusCircle, History, Maximize2, Minimize2 } from "lucide-react";

interface ChatHeaderProps {
  isOnline?: boolean;
  activeContext: "travel" | "logistics";
  onContextChange: (mode: "travel" | "logistics") => void;
  onNewChat: () => void;
  onToggleHistory: () => void;
  onMinimize: () => void;
  onClose: () => void;
  isFullScreen?: boolean;
  onToggleFullScreen?: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  isOnline,
  activeContext,
  onContextChange,
  onNewChat,
  onToggleHistory,
  onMinimize,
  onClose,
  isFullScreen = false,
  onToggleFullScreen,
}) => {
  return (
    <div className={`bg-slate-900 border-b border-slate-800 p-3.5 flex flex-col space-y-2 select-none ${isFullScreen ? "rounded-none" : "rounded-t-2xl"}`}>
      {/* Top Bar: Brand, Status, Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center shadow-md shadow-sky-500/20">
            {activeContext === "travel" ? (
              <Plane className="w-4 h-4 text-white" />
            ) : (
              <Package className="w-4 h-4 text-white" />
            )}
          </div>
          <div>
            <span className="font-bold text-sm text-white tracking-tight block">
              {activeContext === "travel" ? "✈️ Travel Chat" : "📦 Logistics Chat"}
            </span>
            <span className="text-[10px] text-slate-400 block">
              {activeContext === "travel"
                ? "Itineraries • Flights • Hotels • Weather"
                : "Shipments • Telemetry • Freight Tracking"}
            </span>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center space-x-1">
          <button
            type="button"
            onClick={onToggleHistory}
            title="Chat History"
            aria-label="Chat History"
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <History className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={onNewChat}
            title={activeContext === "travel" ? "New Travel Chat" : "New Logistics Chat"}
            aria-label={activeContext === "travel" ? "New Travel Chat" : "New Logistics Chat"}
            className="p-1.5 text-slate-400 hover:text-sky-400 hover:bg-slate-800 rounded-lg transition-colors flex items-center space-x-1"
          >
            <PlusCircle className="w-4 h-4" />
          </button>

          {/* Full Screen / Exit Full Screen Control */}
          <button
            type="button"
            onClick={onToggleFullScreen}
            title={isFullScreen ? "Exit Full Screen" : "Full Screen"}
            aria-label={isFullScreen ? "Exit full screen" : "Enter full screen"}
            className="p-1.5 text-slate-400 hover:text-sky-400 hover:bg-slate-800 rounded-lg transition-colors flex items-center space-x-1.5"
          >
            {isFullScreen ? (
              <>
                <Minimize2 className="w-4 h-4 text-sky-400" />
                <span className="text-xs font-medium hidden sm:inline text-sky-400">Exit Full Screen</span>
              </>
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </button>

          <button
            type="button"
            onClick={onMinimize}
            title="Minimize"
            aria-label="Minimize"
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <Minus className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={onClose}
            title="Close"
            aria-label="Close"
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Context Selector Toggle */}
      <div className="flex items-center justify-between bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
        <span className="text-[10px] text-slate-400 pl-2 font-medium">Select Chat Box:</span>
        <div className="flex items-center space-x-1">
          <button
            type="button"
            onClick={() => onContextChange("travel")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 ${
              activeContext === "travel"
                ? "bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            ✈️ Travel Chat
          </button>
          <button
            type="button"
            onClick={() => onContextChange("logistics")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 ${
              activeContext === "logistics"
                ? "bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            📦 Logistics Chat
          </button>
        </div>
      </div>
    </div>
  );
};
