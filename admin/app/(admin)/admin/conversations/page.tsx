"use client";

import React, { useState, useEffect } from "react";
import { MessageSquare, Search, Database, Loader2, RefreshCw, Bot, User } from "lucide-react";
import { adminApiClient } from "@/lib/api-client";

export default function AdminConversationsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [conversations, setConversations] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Selected Conversation Detail
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<any | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  const fetchConversations = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminApiClient.get<any>("/admin/conversations");
      if (res && res.success) {
        setConversations(res.conversations || []);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to fetch customer conversations from backend.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  const handleOpenConversation = async (convId: string) => {
    setSelectedConvId(convId);
    setIsDetailLoading(true);
    try {
      const res = await adminApiClient.get<any>(`/admin/conversations/${convId}`);
      if (res && res.success) {
        setSelectedDetail(res.conversation);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load conversation messages.");
    } finally {
      setIsDetailLoading(false);
    }
  };

  const filteredConversations = conversations.filter((c) => {
    const term = searchTerm.toLowerCase();
    return (
      c.title?.toLowerCase().includes(term) ||
      c.customer_email?.toLowerCase().includes(term) ||
      c.id?.toLowerCase().includes(term) ||
      c.last_message?.toLowerCase().includes(term) ||
      c.created_at?.toLowerCase().includes(term)
    );
  });


  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <MessageSquare className="w-6 h-6 text-indigo-400" />
            <span>Customer AI Conversations</span>
            {isLoading && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            PostgreSQL-persisted chat transcripts with intent classification and tool execution telemetry.
          </p>
        </div>

        <button
          onClick={fetchConversations}
          disabled={isLoading}
          className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors self-start sm:self-auto"
          title="Refresh List"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Search */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by customer email, title, conversation ID..."
            className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Two Column Layout: List & Detail View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Conversations List */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 overflow-hidden">
          <h3 className="text-sm font-bold text-white mb-3">Saved Conversations ({filteredConversations.length})</h3>
          
          {isLoading ? (
            <div className="py-12 text-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              <p className="text-xs">Fetching conversations from PostgreSQL...</p>
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="py-12 text-center text-slate-500">
              <Database className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
              <p className="text-xs">No conversations recorded yet</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {filteredConversations.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => handleOpenConversation(c.id)}
                  aria-pressed={selectedConvId === c.id}
                  className={`w-full text-left p-3 rounded-xl border transition-all cursor-pointer text-xs ${
                    selectedConvId === c.id
                      ? "bg-indigo-500/10 border-indigo-500 text-white"
                      : "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700"
                  }`}
                >
                  <div className="font-bold text-indigo-300 truncate mb-1">{c.title}</div>
                  <div className="text-[11px] text-slate-400 flex items-center justify-between">
                    <span>{c.customer_email}</span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                      {c.message_count} msgs
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Selected Conversation Detail Viewer */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6">
          {!selectedConvId ? (
            <div className="py-24 text-center text-slate-500">
              <MessageSquare className="w-10 h-10 mx-auto mb-3 opacity-30 text-indigo-400" />
              <p className="text-sm font-semibold text-slate-300">Select a conversation transcript</p>
              <p className="text-xs text-slate-500 mt-1">
                Click any conversation from the list to view full AI interaction messages.
              </p>
            </div>
          ) : isDetailLoading ? (
            <div className="py-24 text-center text-slate-500">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-indigo-400" />
              <p className="text-xs">Loading conversation transcript from database...</p>
            </div>
          ) : selectedDetail ? (
            <div className="space-y-4">
              <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-white">{selectedDetail.title}</h3>
                  <p className="text-xs text-slate-400">Customer: {selectedDetail.customer_email}</p>
                </div>
                <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {selectedDetail.status}
                </span>
              </div>

              {/* Messages Timeline */}
              <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                {selectedDetail.messages?.map((m: any, idx: number) => (
                  <div
                    key={idx}
                    className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed ${
                        m.role === "user"
                          ? "bg-indigo-600 text-white rounded-br-sm"
                          : "bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-sm"
                      }`}
                    >
                      <div className="flex items-center justify-between font-semibold text-[11px] mb-1 opacity-80 gap-2">
                        <div className="flex items-center space-x-1.5">
                          {m.role === "user" ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3 text-indigo-400" />}
                          <span>{m.role === "user" ? "Customer" : "Travelogix AI Assistant"}</span>
                        </div>
                        {m.intent && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] bg-indigo-500/20 text-indigo-300 font-mono">
                            {m.intent}
                          </span>
                        )}
                      </div>
                      <div className="whitespace-pre-wrap">{m.content}</div>
                      <div className="mt-2 pt-1 border-t border-white/10 flex items-center justify-between text-[10px] opacity-70">
                        <span>{m.source || "travelogix_ops"} ({m.mode || "live"})</span>
                        <span>{m.created_at ? new Date(m.created_at).toLocaleTimeString() : ""}</span>
                      </div>

                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
