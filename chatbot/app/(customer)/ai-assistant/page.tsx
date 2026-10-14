"use client";

import React from "react";
import { Compass, Sparkles, MessageSquare, ArrowRight } from "lucide-react";
import Link from "next/link";
import { CustomerChatbot } from "@/components/chatbot/CustomerChatbot";

export default function AiAssistantPage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] bg-slate-950 text-slate-100 px-4 py-8 relative overflow-hidden">
      {/* Subtle ambient lighting */}
      <div className="absolute top-1/3 left-1/3 w-[450px] h-[450px] bg-gradient-to-tr from-sky-600/10 via-blue-600/10 to-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Clean Background Landing Prompt */}
      <div className="max-w-2xl text-center space-y-6 relative z-10 sm:-mt-12">
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-semibold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Multi-Agent AI Assistant</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
          Travel &amp; Logistics in <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-400">One Chat</span>
        </h1>

        <p className="text-sm sm:text-base text-slate-400 max-w-lg mx-auto leading-relaxed">
          Use the floating Travelogix AI Assistant on the right side of your screen to plan trips, look up itineraries, and track freight consignments in real time.
        </p>
      </div>

      {/* Floating Customer AI Assistant Panel Mounted on Right */}
      <CustomerChatbot initialOpen={true} />
    </div>
  );
}
