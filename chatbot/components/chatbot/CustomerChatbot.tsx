"use client";

import React, { useState, useRef, useEffect } from "react";
import { Bot, Sparkles, Loader2, Compass } from "lucide-react";
import { ChatHeader } from "./ChatHeader";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ChatHistoryDrawer } from "./ChatHistoryDrawer";
import { apiClient } from "@/lib/api-client";

interface MessageItem {
  role: "user" | "assistant";
  content: string;
  intent?: string;
  provenance?: {
    source?: string;
    mode?: string;
    is_mock?: boolean;
    fetched_at?: string;
  };
  data?: any;
}

interface CustomerChatbotProps {
  initialOpen?: boolean;
}

export const CustomerChatbot: React.FC<CustomerChatbotProps> = ({ initialOpen = true }) => {
  const [isOpen, setIsOpen] = useState(initialOpen);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 450, height: 650 });
  const [isResizing, setIsResizing] = useState(false);
  const resizeStartRef = useRef<{ startX: number; startY: number; startW: number; startH: number } | null>(null);

  const [isOnline, setIsOnline] = useState(true);
  const [contextMode, setContextMode] = useState<"travel" | "logistics">("travel");

  const [inputMessage, setInputMessage] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // Separate conversation IDs for Travel vs Logistics
  const [travelConversationId, setTravelConversationId] = useState<string | null>(null);
  const [logisticsConversationId, setLogisticsConversationId] = useState<string | null>(null);

  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [activeTrackingId, setActiveTrackingId] = useState<string | null>(null);

  // Separate message histories for Travel Chat vs Logistics Chat
  const [travelMessages, setTravelMessages] = useState<MessageItem[]>([
    {
      role: "assistant",
      content:
        "Hello! Welcome to **Travelogix Travel AI** ✈️\n\nI can help you plan multi-day trip itineraries, find flights, compare hotels, check train schedules, intercity buses, and local weather.\n\nHow can I help you plan your trip today?",
    },
  ]);

  const [logisticsMessages, setLogisticsMessages] = useState<MessageItem[]>([
    {
      role: "assistant",
      content:
        "Hello! Welcome to **Travelogix Freight & Logistics AI** 📦\n\nI can help you track freight consignments with verified telemetry, register new shipments, check driver/vehicle assignments, and monitor delivery milestones.\n\nHow can I help you with your logistics today?",
    },
  ]);

  // Derived active state based on contextMode
  const activeConversationId = contextMode === "travel" ? travelConversationId : logisticsConversationId;
  const activeMessages = contextMode === "travel" ? travelMessages : logisticsMessages;

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen && !isMinimized) {
      scrollToBottom();
    }
  }, [travelMessages, logisticsMessages, contextMode, isGenerating, isOpen, isMinimized, isFullScreen]);

  // Handle Bottom-Right Corner Resize Drag
  const handleResizeStart = (e: React.MouseEvent | React.TouchEvent) => {
    if (isFullScreen) return;
    e.preventDefault();
    e.stopPropagation();

    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

    resizeStartRef.current = {
      startX: clientX,
      startY: clientY,
      startW: dimensions.width,
      startH: dimensions.height,
    };
    setIsResizing(true);
  };

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent | TouchEvent) => {
      if (!resizeStartRef.current) return;
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

      const deltaX = clientX - resizeStartRef.current.startX;
      const deltaY = clientY - resizeStartRef.current.startY;

      const maxW = Math.min(700, window.innerWidth - 40);
      const maxH = window.innerHeight - 40;

      const newW = Math.min(Math.max(320, resizeStartRef.current.startW + deltaX), maxW);
      const newH = Math.min(Math.max(450, resizeStartRef.current.startH + deltaY), maxH);

      setDimensions({ width: newW, height: newH });
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      resizeStartRef.current = null;
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    window.addEventListener("touchmove", handleMouseMove);
    window.addEventListener("touchend", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("touchmove", handleMouseMove);
      window.removeEventListener("touchend", handleMouseUp);
    };
  }, [isResizing]);

  // Check Backend Health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await apiClient.get<any>("/health");
        setIsOnline(Boolean(res && (res.status === "ok" || res.status === "healthy" || res.service)));
      } catch (e) {
        setIsOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Handle URL intent search parameter on mount
  const intentProcessedRef = useRef(false);
  useEffect(() => {
    if (typeof window !== "undefined" && !intentProcessedRef.current) {
      intentProcessedRef.current = true;
      const params = new URLSearchParams(window.location.search);
      const intent = params.get("intent");
      if (intent) {
        let initialPrompt = "";
        let targetMode: "travel" | "logistics" = "travel";

        if (intent === "travel" || intent === "trip") {
          targetMode = "travel";
          initialPrompt = "Plan 5 days trip to Goa";
        } else if (intent === "hotel") {
          targetMode = "travel";
          initialPrompt = "Find hotels in Goa";
        } else if (intent === "train") {
          targetMode = "travel";
          initialPrompt = "Find train running status and schedules";
        } else if (intent === "bus") {
          targetMode = "travel";
          initialPrompt = "Find bus options";
        } else if (intent === "tracking" || intent === "shipment") {
          targetMode = "logistics";
          initialPrompt = "Track TLX-2026-100001";
        }
        if (initialPrompt) {
          setContextMode(targetMode);
          setTimeout(() => {
            handleSend(initialPrompt, targetMode);
          }, 50);
        }
      }
    }
  }, []);

  const handleSend = async (messageText?: string, overrideMode?: "travel" | "logistics") => {
    const textToSend = (messageText || inputMessage).trim();
    if (!textToSend || isGenerating) return;

    const modeToUse = overrideMode || contextMode;
    const currentConvId = modeToUse === "travel" ? travelConversationId : logisticsConversationId;

    // Append user message to the active mode's conversation
    if (modeToUse === "travel") {
      setTravelMessages((prev) => [...prev, { role: "user", content: textToSend }]);
    } else {
      setLogisticsMessages((prev) => [...prev, { role: "user", content: textToSend }]);
    }

    setInputMessage("");
    setIsGenerating(true);

    try {
      const response = await apiClient.sendChatMessage(textToSend, currentConvId);

      if (response && (response.reply || response.message)) {
        const replyContent = response.reply || response.message;

        if (response.conversation_id) {
          if (modeToUse === "travel") {
            setTravelConversationId(response.conversation_id);
          } else {
            setLogisticsConversationId(response.conversation_id);
          }
        }

        if (response.tracking_id) {
          setActiveTrackingId(response.tracking_id);
        }

        const newAssistantMsg: MessageItem = {
          role: "assistant",
          content: replyContent,
          intent: response.intent,
          provenance: response.provenance,
          data: response.data,
        };

        if (modeToUse === "travel") {
          setTravelMessages((prev) => [...prev, newAssistantMsg]);
        } else {
          setLogisticsMessages((prev) => [...prev, newAssistantMsg]);
        }
      } else {
        throw new Error("Invalid response format received from Travelogix API.");
      }
    } catch (err: any) {
      const errorMsg: MessageItem = {
        role: "assistant",
        content: `We encountered an issue communicating with Travelogix AI: ${err.message || "Backend service unavailable"}.`,
      };

      if (modeToUse === "travel") {
        setTravelMessages((prev) => [...prev, errorMsg]);
      } else {
        setLogisticsMessages((prev) => [...prev, errorMsg]);
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleNewChat = async () => {
    const modeToUse = contextMode;
    const title = modeToUse === "travel" ? "New Travel Chat" : "New Logistics Chat";

    let newConvId: string | null = null;
    try {
      const res = await apiClient.createConversation(title);
      if (res && res.conversation_id) {
        newConvId = res.conversation_id;
      }
    } catch (e) {
      newConvId = null;
    }

    if (modeToUse === "travel") {
      setTravelConversationId(newConvId);
      setTravelMessages([
        {
          role: "assistant",
          content:
            "Started a new **Travel Chat** ✈️\n\nHow can I help you plan your next trip?",
        },
      ]);
    } else {
      setLogisticsConversationId(newConvId);
      setLogisticsMessages([
        {
          role: "assistant",
          content:
            "Started a new **Logistics Chat** 📦\n\nWhich shipment or consignment would you like to track or manage?",
        },
      ]);
    }
  };

  const handleSelectHistoryConversation = async (convId: string) => {
    try {
      const res = await apiClient.getConversationDetail(convId);
      if (res && res.success && res.conversation) {
        const mappedMsgs = (res.conversation.messages || []).map((m: any) => ({
          role: m.role,
          content: m.content,
          intent: m.intent,
          provenance: { source: m.source || "travelogix_database", mode: m.mode || "live" },
        }));
        if (mappedMsgs.length > 0) {
          if (contextMode === "travel") {
            setTravelConversationId(convId);
            setTravelMessages(mappedMsgs);
          } else {
            setLogisticsConversationId(convId);
            setLogisticsMessages(mappedMsgs);
          }
        }
      }
    } catch (e: any) {
      const errorMsg: MessageItem = {
        role: "assistant",
        content: `I could not open that saved conversation: ${e?.message || "unknown error"}.`,
      };
      if (contextMode === "travel") {
        setTravelMessages((prev) => [...prev, errorMsg]);
      } else {
        setLogisticsMessages((prev) => [...prev, errorMsg]);
      }
    }
  };

  // Minimized Trigger Button
  if (!isOpen || isMinimized) {
    return (
      <div className="fixed bottom-5 right-5 z-50 select-none">
        <button
          type="button"
          onClick={() => {
            setIsOpen(true);
            setIsMinimized(false);
            setIsFullScreen(false);
          }}
          className="group flex items-center space-x-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-bold text-xs shadow-2xl shadow-sky-500/30 border border-sky-400/30 transition-all hover:scale-105 active:scale-95"
        >
          <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <span>Travelogix AI</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </button>
      </div>
    );
  }

  return (
    <div
      style={
        isFullScreen
          ? {
              position: "fixed",
              top: 0,
              right: 0,
              bottom: 0,
              left: 0,
              width: "100vw",
              height: "100vh",
              maxWidth: "100vw",
              maxHeight: "100vh",
              zIndex: 50,
            }
          : {
              position: "fixed",
              right: "20px",
              bottom: "20px",
              width: `${dimensions.width}px`,
              height: `${dimensions.height}px`,
              maxWidth: "calc(100vw - 20px)",
              maxHeight: "calc(100vh - 20px)",
              zIndex: 50,
            }
      }
      className={`bg-slate-950 border border-slate-800 shadow-2xl flex flex-col overflow-hidden font-sans relative ${
        isFullScreen ? "rounded-none border-0" : "rounded-2xl"
      } ${isResizing ? "select-none" : ""}`}
    >
      {/* Header */}
      <ChatHeader
        isOnline={isOnline}
        activeContext={contextMode}
        onContextChange={(mode) => setContextMode(mode)}
        onNewChat={handleNewChat}
        onToggleHistory={() => setIsHistoryOpen(!isHistoryOpen)}
        onMinimize={() => setIsMinimized(true)}
        onClose={() => setIsOpen(false)}
        isFullScreen={isFullScreen}
        onToggleFullScreen={() => setIsFullScreen((prev) => !prev)}
      />

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-3.5 relative">
        {activeMessages.map((msg, index) => (
          <ChatMessage key={index} message={msg} />
        ))}

        {isGenerating && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-2xl p-3.5 bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-sm flex items-center space-x-3 text-xs">
              <Loader2 className="w-4 h-4 text-sky-400 animate-spin shrink-0" />
              <div className="text-slate-400">
                <span className="text-slate-200 font-semibold">Travelogix AI is thinking:</span> Classifying intent &amp; executing tools...
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />

        {/* History Drawer overlay */}
        <ChatHistoryDrawer
          isOpen={isHistoryOpen}
          onClose={() => setIsHistoryOpen(false)}
          onSelectConversation={handleSelectHistoryConversation}
        />
      </div>

      {/* Chat Input Bar */}
      <ChatInput isGenerating={isGenerating} onSend={(msg) => handleSend(msg)} />

      {/* Resize Handle in Bottom-Right Corner (Side Mode only) */}
      {!isFullScreen && (
        <div
          onMouseDown={handleResizeStart}
          onTouchStart={handleResizeStart}
          aria-label="Resize chatbot"
          title="Resize chatbot"
          role="button"
          tabIndex={0}
          className="absolute bottom-1 right-1 w-4 h-4 cursor-se-resize flex items-center justify-center text-slate-500 hover:text-sky-400 z-20 select-none group"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
            <path
              d="M14 14H12V12H14V14ZM14 10H12V8H14V10ZM10 14H8V12H10V14ZM14 6H12V4H14V6ZM10 10H8V8H10V10ZM6 14H4V12H6V14Z"
              opacity="0.6"
            />
          </svg>
        </div>
      )}
    </div>
  );
};
