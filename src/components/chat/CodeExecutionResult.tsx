"use client";

import React, { useState } from "react";
import { Terminal, Copy, Check, AlertTriangle, ShieldCheck, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";

interface CodeExecutionResultProps {
  result: {
    language: string;
    stdout: string;
    stderr: string;
    exit_code?: number;
    execution_time?: number;
  };
}

export function CodeExecutionResult({ result }: CodeExecutionResultProps) {
  const [copiedType, setCopiedType] = useState<"stdout" | "stderr" | null>(null);

  if (!result) return null;

  const handleCopy = async (text: string, type: "stdout" | "stderr") => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedType(type);
      setTimeout(() => setCopiedType(null), 2000);
    } catch (err) {
      console.error("Failed to copy console text:", err);
    }
  };

  const hasStdout = !!result.stdout.trim();
  const hasStderr = !!result.stderr.trim();
  const success = result.exit_code === 0;

  return (
    <div className="w-full my-4 rounded-xl border border-border-subtle bg-slate-950 text-slate-100 overflow-hidden shadow-lg select-text font-mono text-xs">
      {/* Console Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800 select-none">
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-300">
            Python Sandbox Output
          </span>
          <span className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <ShieldCheck className="w-2.5 h-2.5" />
            Isolated
          </span>
        </div>

        <div className="flex items-center gap-3 text-[10px] text-slate-400">
          {result.execution_time !== undefined && (
            <span className="flex items-center gap-1">
              <Cpu className="w-3 h-3 text-slate-500" />
              {result.execution_time.toFixed(3)}s
            </span>
          )}
          <span
            className={cn(
              "px-2 py-0.5 rounded text-[9px] font-bold border",
              success
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                : "bg-red-500/10 border-red-500/20 text-red-400"
            )}
          >
            exit code: {result.exit_code ?? (success ? 0 : 1)}
          </span>
        </div>
      </div>

      {/* Output Panels */}
      <div className="p-4 space-y-4">
        {/* Stdout Console */}
        {hasStdout && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-slate-400 text-[10px] select-none">
              <span className="uppercase tracking-wider font-bold text-slate-500">STDOUT</span>
              <button
                onClick={() => handleCopy(result.stdout, "stdout")}
                className="hover:text-slate-200 transition p-1 rounded hover:bg-slate-900 cursor-pointer"
                title="Copy stdout"
              >
                {copiedType === "stdout" ? (
                  <Check className="w-3 h-3 text-emerald-400" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
              </button>
            </div>
            <pre className="p-3 rounded-lg bg-slate-900/50 border border-slate-900 text-slate-200 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-60 scrollbar-thin">
              {result.stdout}
            </pre>
          </div>
        )}

        {/* Stderr Console */}
        {hasStderr && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-red-400 text-[10px] select-none">
              <span className="uppercase tracking-wider font-bold text-red-900 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 text-red-500" />
                STDERR / EXECUTION EXCEPTION
              </span>
              <button
                onClick={() => handleCopy(result.stderr, "stderr")}
                className="hover:text-red-200 transition p-1 rounded hover:bg-slate-900 cursor-pointer"
                title="Copy stderr"
              >
                {copiedType === "stderr" ? (
                  <Check className="w-3 h-3 text-emerald-400" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
              </button>
            </div>
            <pre className="p-3 rounded-lg bg-red-950/20 border border-red-500/10 text-red-300 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-48 scrollbar-thin">
              {result.stderr}
            </pre>
          </div>
        )}

        {/* Empty output state */}
        {!hasStdout && !hasStderr && (
          <div className="py-4 text-center text-slate-500 italic select-none">
            [Code execution completed with no output]
          </div>
        )}
      </div>
    </div>
  );
}
