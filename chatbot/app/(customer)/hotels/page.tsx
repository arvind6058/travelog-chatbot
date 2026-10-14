"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Hotel, Bot, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function HotelsRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect immediately: the previous 1.5s delay was dead time on every
    // click and could double-navigate if the CTA was pressed mid-timer.
    router.replace("/ai-assistant?intent=hotel");
  }, [router]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[70vh] px-4 text-center">
      <div className="w-16 h-16 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center mb-4">
        <Hotel className="w-8 h-8 text-sky-400" />
      </div>
      <h2 className="text-xl font-bold text-white mb-2">Travelogix is Chatbot-First</h2>
      <p className="text-sm text-slate-400 max-w-md mb-6">
        Hotel search and reservation discovery happen conversationally through our AI Assistant. Taking you there now…
      </p>
      <Link
        href="/ai-assistant?intent=hotel"
        className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-medium text-sm transition-all"
      >
        <Bot className="w-4 h-4" />
        <span>Open Hotel AI Assistant</span>
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  );
}
