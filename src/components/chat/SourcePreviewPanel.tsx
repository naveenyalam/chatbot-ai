"use client";

import React from "react";
import { X, FileText, ExternalLink, Bookmark, Check } from "lucide-react";
import { CitationSource } from "@/types";

interface SourcePreviewPanelProps {
  source: CitationSource | null;
  onClose: () => void;
}

export function SourcePreviewPanel({ source, onClose }: SourcePreviewPanelProps) {
  const [copied, setCopied] = React.useState(false);

  if (!source) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(source.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-surface-elevated border-l border-border shadow-2xl glass-panel p-5 flex flex-col animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div className="flex items-center gap-2 min-w-0">
          <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <FileText className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <h3 className="text-xs font-bold text-foreground truncate">{source.filename}</h3>
            <p className="text-[10px] text-muted-foreground">
              {source.page > 0 ? `Page ${source.page}` : "Retrieved Document Chunk"}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Relevance Indicator */}
      <div className="py-3 border-b border-border flex items-center justify-between">
        <span className="text-[11px] text-muted-foreground font-medium">Retrieval Match</span>
        <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold">
          High Relevance
        </span>
      </div>

      {/* Body Content */}
      <div className="flex-1 my-4 overflow-y-auto bg-surface/60 border border-border rounded-xl p-4 font-mono text-xs text-foreground/90 leading-relaxed whitespace-pre-wrap selection:bg-indigo-500/30">
        {source.content}
      </div>

      {/* Actions */}
      <div className="pt-3 border-t border-border flex items-center justify-between gap-2">
        <button
          onClick={handleCopy}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-border bg-surface hover:bg-surface-hover text-xs font-semibold text-foreground transition-all cursor-pointer"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Bookmark className="w-3.5 h-3.5 text-indigo-400" />}
          <span>{copied ? "Copied" : "Copy Excerpt"}</span>
        </button>
        <button
          onClick={onClose}
          className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all cursor-pointer"
        >
          Close
        </button>
      </div>
    </div>
  );
}
