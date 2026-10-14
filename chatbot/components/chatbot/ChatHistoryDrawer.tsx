"use client";

import React, { useState, useEffect } from "react";
import { History, X, Loader2, MessageSquare, Database, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface ChatHistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectConversation: (convId: string) => void;
}

export const ChatHistoryDrawer: React.FC<ChatHistoryDrawerProps> = ({
  isOpen,
  onClose,
  onSelectConversation,
}) => {
  const [conversations, setConversations] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchHistory();
    }
  }, [isOpen]);

  const fetchHistory = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await apiClient.getConversations();
      if (res && res.success) {
        setConversations(res.conversations || []);
      }
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to load your chat history.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="absolute inset-0 z-40 bg-slate-900/95 backdrop-blur-md rounded-2xl p-4 flex flex-col space-y-3 font-sans">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2 text-white font-bold text-xs">
          <History className="w-4 h-4 text-sky-400" />
          <span>PostgreSQL Chat History</span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {isLoading ? (
          <div className="py-12 text-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
            <p className="text-xs">Fetching past conversations...</p>
          </div>
        ) : errorMsg ? (
          <div className="py-12 text-center text-rose-300 px-4">
            <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-2 opacity-70" />
            <p className="text-xs">{errorMsg}</p>
            <button
              type="button"
              onClick={fetchHistory}
              className="mt-3 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-[11px] font-semibold text-slate-200 hover:bg-slate-800 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : conversations.length === 0 ? (
          <div className="py-12 text-center text-slate-500">
            <Database className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-40" />
            <p className="text-xs">No previous chats stored in database</p>
          </div>
        ) : (
          conversations.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => {
                onSelectConversation(c.id);
                onClose();
              }}
              className="w-full text-left p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-sky-500/50 hover:bg-slate-800/60 transition-all text-xs"
            >
              <div className="font-bold text-sky-300 truncate mb-1">{c.title}</div>
              <div className="flex items-center justify-between text-[10px] text-slate-500">
                <span>{c.created_at ? new Date(c.created_at).toLocaleDateString() : ""}</span>
                <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                  {c.message_count || 2} msgs
                </span>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
};
