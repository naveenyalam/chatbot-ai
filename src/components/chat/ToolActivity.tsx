"use client";

import React, { useState } from "react";
import {
  Search,
  Calculator,
  Terminal,
  FileSearch,
  CheckCircle2,
  XCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  Activity,
  AlertCircle,
} from "lucide-react";
import { ToolActivityItem } from "@/types";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

interface ToolActivityProps {
  activity: ToolActivityItem[];
}

const TOOL_ICONS: Record<string, React.ComponentType<any>> = {
  web_search: Search,
  calculator: Calculator,
  code_execution: Terminal,
  document_search: FileSearch,
};

const TOOL_COLORS: Record<string, string> = {
  web_search: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  calculator: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  code_execution: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  document_search: "text-amber-400 bg-amber-500/10 border-amber-500/20",
};

export function ToolActivity({ activity }: ToolActivityProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!activity || activity.length === 0) return null;

  const toggleExpand = (idx: number) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  return (
    <div className="w-full my-4 rounded-xl border border-border-subtle bg-surface-secondary/20 overflow-hidden shadow-sm backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-surface-secondary/40 border-b border-border-subtle/30">
        <div className="flex items-center gap-2">
          <div className="relative flex items-center justify-center w-5 h-5">
            <Activity className="w-3.5 h-3.5 text-accent animate-pulse" />
            <span className="absolute inline-flex h-full w-full rounded-full bg-accent/20 animate-ping opacity-75" />
          </div>
          <span className="text-[10px] font-bold text-text-primary uppercase tracking-wider">
            Agent Actions & Process ({activity.length})
          </span>
        </div>
      </div>

      {/* List of actions */}
      <div className="divide-y divide-border-subtle/20">
        {activity.map((item, idx) => {
          const Icon = TOOL_ICONS[item.tool] || Activity;
          const colorClass = TOOL_COLORS[item.tool] || "text-accent bg-accent/10 border-accent/20";
          const isExpanded = expandedIndex === idx;

          return (
            <div
              key={idx}
              className={cn(
                "transition-colors duration-200",
                isExpanded ? "bg-surface-secondary/10" : "hover:bg-surface-secondary/5"
              )}
            >
              {/* Row Header */}
              <div
                onClick={() => toggleExpand(idx)}
                className="flex items-center justify-between px-4 py-3 cursor-pointer select-none"
              >
                <div className="flex items-center gap-3 min-w-0">
                  {/* Tool Icon Badge */}
                  <div
                    className={cn(
                      "w-7 h-7 rounded-lg border flex items-center justify-center flex-shrink-0 transition-transform duration-200",
                      colorClass,
                      isExpanded && "scale-105"
                    )}
                  >
                    <Icon className="w-4 h-4" />
                  </div>

                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-text-primary truncate">
                      {item.label}
                    </p>
                    <p className="text-[10px] text-text-muted mt-0.5 font-mono">
                      tool: {item.tool}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {/* Duration Badge */}
                  {item.duration !== undefined && (
                    <span className="text-[9px] font-mono text-text-muted bg-surface-secondary/50 border border-border-subtle/20 px-1.5 py-0.5 rounded flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5 text-text-muted/60" />
                      {item.duration.toFixed(2)}s
                    </span>
                  )}

                  {/* Status indicator */}
                  {item.status === "running" ? (
                    <div className="flex items-center gap-1.5 text-[10px] font-semibold text-accent">
                      <span className="relative flex h-1.5 w-1.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-accent"></span>
                      </span>
                      <span className="hidden sm:inline">Executing</span>
                    </div>
                  ) : item.status === "complete" ? (
                    <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-4.5 h-4.5 text-red-400 flex-shrink-0" />
                  )}

                  {/* Accordion toggle */}
                  {isExpanded ? (
                    <ChevronUp className="w-3.5 h-3.5 text-text-muted" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5 text-text-muted" />
                  )}
                </div>
              </div>

              {/* Accordion Content */}
              <AnimatePresence initial={false}>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2, ease: "easeInOut" }}
                    className="overflow-hidden border-t border-border-subtle/10"
                  >
                    <div className="px-4 pb-4 pt-2 text-xs space-y-3 font-mono">
                      {/* Tool Inputs/Outputs */}
                      {item.preview && (
                        <div>
                          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider block mb-1">
                            Execution Preview
                          </span>
                          <div className="p-2.5 rounded-lg border border-border-subtle/40 bg-surface-primary/40 text-text-muted text-[11px] leading-relaxed overflow-x-auto whitespace-pre-wrap max-h-36 scrollbar-thin">
                            {item.preview}
                          </div>
                        </div>
                      )}

                      {item.data && (
                        <div>
                          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider block mb-1">
                            Structured Output Data
                          </span>
                          <pre className="p-2.5 rounded-lg border border-border-subtle/40 bg-surface-primary/40 text-text-primary text-[10px] overflow-x-auto max-h-48 scrollbar-thin">
                            {JSON.stringify(item.data, null, 2)}
                          </pre>
                        </div>
                      )}

                      {item.error && (
                        <div className="p-2.5 rounded-lg border border-red-500/10 bg-red-500/5 text-red-400 text-[11px] flex gap-2">
                          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="font-bold block mb-0.5">Execution Failed</span>
                            <p>{item.error}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </div>
  );
}
