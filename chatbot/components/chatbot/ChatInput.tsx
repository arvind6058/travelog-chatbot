"use client";

import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, Loader2 } from "lucide-react";

interface ChatInputProps {
  isGenerating: boolean;
  onSend: (message: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({ isGenerating, onSend }) => {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-grow height based on content up to max-height (180px)
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    const scrollHeight = textarea.scrollHeight;
    textarea.style.height = `${Math.min(Math.max(scrollHeight, 72), 180)}px`;
  }, [text]);

  const handleSendClick = () => {
    const trimmed = text.trim();
    if (!trimmed || isGenerating) return;
    onSend(trimmed);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "72px";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendClick();
    }
  };

  return (
    <div className="p-3 bg-slate-950 border-t border-slate-800/80 shrink-0">
      <div className="relative w-full bg-slate-900/90 border border-slate-700/60 rounded-3xl focus-within:border-sky-500/80 focus-within:ring-1 focus-within:ring-sky-500/50 shadow-xl transition-all flex flex-col justify-between overflow-hidden">
        {/* Large Multiline Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          disabled={isGenerating}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message here..."
          className="w-full px-4 pt-3.5 pb-12 bg-transparent text-sm text-slate-100 placeholder-slate-400 focus:outline-none resize-none overflow-y-auto max-h-[180px] min-h-[72px] leading-relaxed"
        />

        {/* Send Button on bottom-right inside composer */}
        <div className="absolute bottom-2.5 right-3 flex items-center pointer-events-auto">
          <button
            type="button"
            disabled={!text.trim() || isGenerating}
            onClick={handleSendClick}
            className="w-8 h-8 rounded-full bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center disabled:opacity-30 disabled:hover:bg-blue-600 transition-all shadow-md shadow-blue-500/30 shrink-0 cursor-pointer"
          >
            {isGenerating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            )}
          </button>
        </div>
      </div>
      <div className="text-[10px] text-center text-slate-500 mt-1.5">
        Press Enter to send, Shift + Enter for new line &bull; Travelogix AI
      </div>
    </div>
  );
};
