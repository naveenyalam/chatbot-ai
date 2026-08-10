"use client";

import React, { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, FileText, Bookmark } from "lucide-react";

export interface CitationSource {
  index: number;
  filename: string;
  page: number;
  content: string;
}

interface SourcePanelProps {
  isOpen: boolean;
  onClose: () => void;
  sources: CitationSource[];
  highlightIndex?: number;
}

export function SourcePanel({ isOpen, onClose, sources, highlightIndex }: SourcePanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (highlightIndex !== undefined && panelRef.current) {
      const targetElement = document.getElementById(`source-citation-${highlightIndex}`);
      if (targetElement) {
        targetElement.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [highlightIndex, isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
          />

          {/* Drawer container */}
          <motion.div
            ref={panelRef}
            initial={{ x: "100%", opacity: 0.9 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "100%", opacity: 0.9 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="relative w-full max-w-md h-full bg-zinc-950/95 border-l border-white/10 flex flex-col shadow-2xl z-10"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-emerald-500/10 text-emerald-400 rounded-md">
                  <Bookmark size={16} />
                </div>
                <h3 className="text-sm font-semibold text-white">Retrieved Sources</h3>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 hover:bg-white/5 rounded-lg text-white/40 hover:text-white transition"
              >
                <X size={16} />
              </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {sources.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-white/30 gap-2">
                  <FileText size={28} strokeWidth={1.5} />
                  <span className="text-xs">No active source citations found.</span>
                </div>
              ) : (
                sources.map((src) => {
                  const isHighlighted = highlightIndex === src.index;
                  return (
                    <motion.div
                      id={`source-citation-${src.index}`}
                      key={src.index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`p-4 rounded-xl border transition-all duration-300 ${
                        isHighlighted
                          ? "border-emerald-500 bg-emerald-500/[0.03] shadow-[0_0_15px_rgba(16,185,129,0.05)]"
                          : "border-white/5 bg-white/[0.01]"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="flex-shrink-0 flex items-center justify-center w-5 h-5 bg-white/10 text-white/80 rounded text-[10px] font-bold">
                            {src.index}
                          </span>
                          <span className="text-xs font-semibold text-white/90 truncate max-w-[240px]">
                            {src.filename}
                          </span>
                        </div>
                        <span className="text-[10px] text-white/40 bg-white/5 px-1.5 py-0.5 rounded">
                          Page {src.page}
                        </span>
                      </div>
                      <p className="text-xs text-white/60 leading-relaxed break-words whitespace-pre-wrap select-text selection:bg-emerald-500/25">
                        &ldquo;{src.content}&rdquo;
                      </p>
                    </motion.div>
                  );
                })
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
