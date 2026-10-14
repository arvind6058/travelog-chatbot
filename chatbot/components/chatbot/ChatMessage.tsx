"use client";

import React from "react";
import { Bot, User } from "lucide-react";
import { TrackingResultCard } from "./TrackingResultCard";

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

interface ChatMessageProps {
  message: MessageItem;
}

/**
 * Unescape backslash-escaped markdown markers (e.g. \*\* -> **, \# -> #, \* -> *)
 * that might have been introduced during JSON transport or string formatting.
 */
const unescapeMarkdown = (text: string): string => {
  if (!text) return "";
  return text.replace(/\\(\*|_|#|-|\+|`|~|\[|\]|\(|\))/g, "$1");
};

/**
 * Render inline markdown tokens (bold, italic, code, links).
 */
const renderInlineMarkup = (text: string): React.ReactNode => {
  const cleanText = unescapeMarkdown(text);
  
  // Tokenize by inline elements: bold (** or __), code (`), italic (* or _), links ([text](url))
  const parts = cleanText.split(/(\*\*.*?\*\*|__.*?__|`.*?`|\*.*?\*|_.*?_|\[.*?\]\(.*?\))/g);
  
  return parts.map((part, index) => {
    if (!part) return null;

    // Bold **text** or __text__
    if ((part.startsWith("**") && part.endsWith("**") && part.length >= 4) ||
        (part.startsWith("__") && part.endsWith("__") && part.length >= 4)) {
      const inner = part.slice(2, -2);
      return (
        <strong key={index} className="text-white font-semibold">
          {renderInlineMarkup(inner)}
        </strong>
      );
    }

    // Italic *text* or _text_
    if ((part.startsWith("*") && part.endsWith("*") && part.length >= 2) ||
        (part.startsWith("_") && part.endsWith("_") && part.length >= 2)) {
      const inner = part.slice(1, -1);
      return (
        <em key={index} className="text-slate-300 italic">
          {renderInlineMarkup(inner)}
        </em>
      );
    }

    // Inline Code `text`
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      const inner = part.slice(1, -1);
      return (
        <code key={index} className="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-sky-300 font-medium">
          {inner}
        </code>
      );
    }

    // Link [text](url)
    const linkMatch = part.match(/^\[(.*?)\]\((.*?)\)$/);
    if (linkMatch) {
      const [, linkText, linkUrl] = linkMatch;
      return (
        <a
          key={index}
          href={linkUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sky-400 underline hover:text-sky-300 font-medium"
        >
          {linkText}
        </a>
      );
    }

    return part;
  });
};

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === "user";
  const isTracking = message.intent === "SHIPMENT_TRACKING" || message.content.includes("Consignment Status");

  const renderFormattedContent = (content: string) => {
    const cleaned = unescapeMarkdown(content);

    // Handle multiline code blocks (fenced ``` code blocks)
    const codeBlockSplit = cleaned.split(/(```[\s\S]*?```)/g);

    return (
      <div className="space-y-1.5 text-xs leading-relaxed">
        {codeBlockSplit.map((section, sIdx) => {
          if (section.startsWith("```") && section.endsWith("```")) {
            const rawCodeLines = section.slice(3, -3).trim().split("\n");
            // Drop optional language identifier if present on line 1
            const firstLine = rawCodeLines[0] || "";
            const codeLines = /^[a-zA-Z0-9_-]+$/.test(firstLine.trim()) && rawCodeLines.length > 1
              ? rawCodeLines.slice(1)
              : rawCodeLines;
            return (
              <pre
                key={`code-${sIdx}`}
                className="p-3 my-2 rounded-xl bg-slate-950 border border-slate-800 text-sky-300 font-mono text-[11px] overflow-x-auto whitespace-pre-wrap"
              >
                <code>{codeLines.join("\n")}</code>
              </pre>
            );
          }

          // Process normal text lines outside fenced code blocks
          const lines = section.split("\n");
          return (
            <React.Fragment key={`sec-${sIdx}`}>
              {lines.map((line, idx) => {
                const trimmed = line.trim();
                if (!trimmed) {
                  return <div key={idx} className="h-1" />;
                }

                // Headers (H1, H2, H3, H4)
                if (trimmed.startsWith("### ")) {
                  const headerText = trimmed.substring(4);
                  return (
                    <h3 key={idx} className="text-sm font-bold text-sky-300 mt-2.5 mb-1 flex items-center space-x-1">
                      {renderInlineMarkup(headerText)}
                    </h3>
                  );
                }
                if (trimmed.startsWith("## ")) {
                  const headerText = trimmed.substring(3);
                  return (
                    <h2 key={idx} className="text-base font-bold text-white mt-3 mb-1">
                      {renderInlineMarkup(headerText)}
                    </h2>
                  );
                }
                if (trimmed.startsWith("# ")) {
                  const headerText = trimmed.substring(2);
                  return (
                    <h1 key={idx} className="text-base font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-400 mt-2 mb-1">
                      {renderInlineMarkup(headerText)}
                    </h1>
                  );
                }

                // Bullet points (- or * or •)
                if (trimmed.startsWith("- ") || trimmed.startsWith("* ") || trimmed.startsWith("• ")) {
                  const rawText = trimmed.substring(2);
                  return (
                    <div key={idx} className="flex items-start space-x-2 pl-1 my-0.5">
                      <span className="text-sky-400 mt-0.5 text-[10px] shrink-0">&bull;</span>
                      <span className="text-slate-200">{renderInlineMarkup(rawText)}</span>
                    </div>
                  );
                }

                // Numbered lists (1. , 2. , etc.)
                const numberedMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
                if (numberedMatch) {
                  const [, num, itemText] = numberedMatch;
                  return (
                    <div key={idx} className="flex items-start space-x-2 pl-1 my-0.5">
                      <span className="text-sky-400 font-bold font-mono text-[11px] shrink-0">{num}.</span>
                      <span className="text-slate-200">{renderInlineMarkup(itemText)}</span>
                    </div>
                  );
                }

                // Horizontal dividers
                if (trimmed === "---" || trimmed === "***" || trimmed === "___") {
                  return <hr key={idx} className="border-slate-800 my-2.5" />;
                }

                // Standard Paragraph
                return (
                  <p key={idx} className="text-slate-200">
                    {renderInlineMarkup(line)}
                  </p>
                );
              })}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} font-sans`}>
      <div
        className={`max-w-[88%] sm:max-w-[82%] rounded-2xl p-3.5 shadow-md ${
          isUser
            ? "bg-gradient-to-r from-sky-600 to-blue-600 text-white rounded-br-sm shadow-sky-500/10"
            : "bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-sm"
        }`}
      >
        {!isUser && (
          <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-slate-800/80">
            <div className="flex items-center space-x-1.5 text-sky-400 font-semibold text-[11px]">
              <Bot className="w-3.5 h-3.5" />
              <span>Travelogix AI</span>
            </div>
          </div>
        )}

        {renderFormattedContent(message.content)}

        {/* Embedded Tracking Card if tracking intent */}
        {!isUser && isTracking && (
          <TrackingResultCard data={message.data} trackingId={message.data?.tracking_id} />
        )}
      </div>
    </div>
  );
};
