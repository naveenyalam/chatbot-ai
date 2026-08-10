"use client";

import React, { useState } from "react";
import {
  Code2,
  Play,
  RotateCcw,
  ShieldCheck,
  Terminal as TerminalIcon,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
} from "lucide-react";
import { ToolType } from "@/components/chat/ChatInput";

interface CodeWorkspaceProps {
  onRunCodeInChat: (code: string, lang: string) => void;
}

export function CodeWorkspace({ onRunCodeInChat }: CodeWorkspaceProps) {
  const [language, setLanguage] = useState<"python" | "javascript" | "math">("python");
  const [code, setCode] = useState<string>(
    `# NOVA AI Python Sandbox Demo\ndef calculate_fibonacci(n):\n    sequence = [0, 1]\n    while len(sequence) < n:\n        sequence.append(sequence[-1] + sequence[-2])\n    return sequence[:n]\n\nprint("Fibonacci Sequence:", calculate_fibonacci(10))\nprint("Execution Completed Successfully.")`
  );
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExecute = () => {
    onRunCodeInChat(code, language);
  };

  const handleReset = () => {
    if (language === "python") {
      setCode(`# NOVA AI Python Sandbox Demo\ndef calculate_fibonacci(n):\n    sequence = [0, 1]\n    while len(sequence) < n:\n        sequence.append(sequence[-1] + sequence[-2])\n    return sequence[:n]\n\nprint("Fibonacci Sequence:", calculate_fibonacci(10))`);
    } else if (language === "javascript") {
      setCode(`// NOVA AI JavaScript Sandbox\nconst items = [10, 20, 30, 40, 50];\nconst sum = items.reduce((acc, curr) => acc + curr, 0);\nconsole.log("Calculated Sum:", sum);`);
    } else {
      setCode(`2 * (15 + 35) / 5`);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-6 max-w-7xl mx-auto w-full select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" /> Isolated RestrictedPython Sandbox
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">
            Developer Code Sandbox
          </h1>
          <p className="text-sm text-zinc-400">
            Write and execute safe scripts with instant stdout emission and error handling.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={language}
            onChange={(e) => {
              const lang = e.target.value as any;
              setLanguage(lang);
              if (lang === "javascript") {
                setCode(`// NOVA AI JavaScript Sandbox\nconst items = [10, 20, 30, 40, 50];\nconst sum = items.reduce((acc, curr) => acc + curr, 0);\nconsole.log("Calculated Sum:", sum);`);
              } else if (lang === "math") {
                setCode(`2 * (15 + 35) / 5`);
              } else {
                setCode(`# NOVA AI Python Sandbox Demo\ndef calculate_fibonacci(n):\n    sequence = [0, 1]\n    while len(sequence) < n:\n        sequence.append(sequence[-1] + sequence[-2])\n    return sequence[:n]\n\nprint("Fibonacci Sequence:", calculate_fibonacci(10))`);
              }
            }}
            className="bg-[#0b0f19] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-zinc-200 focus:outline-none focus:border-indigo-500 font-medium"
          >
            <option value="python">Python 3.10 AST</option>
            <option value="javascript">JavaScript V8 Engine</option>
            <option value="math">Math Expression Evaluator</option>
          </select>

          <button
            onClick={handleReset}
            className="p-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
            title="Reset code template"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Editor & Console Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Code Editor Input */}
        <div className="lg:col-span-7 flex flex-col rounded-3xl bg-[#0b0f19]/90 border border-white/10 overflow-hidden shadow-2xl glass-panel">
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-black/40">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-amber-500/80" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
              <span className="text-xs text-zinc-400 font-mono ml-2">main.{language === "python" ? "py" : language === "javascript" ? "js" : "calc"}</span>
            </div>

            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
          </div>

          <div className="p-6 font-mono text-sm">
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              rows={14}
              className="w-full bg-transparent text-zinc-200 placeholder:text-zinc-600 focus:outline-none resize-none font-mono leading-relaxed selection:bg-indigo-500/30"
              spellCheck={false}
            />
          </div>

          <div className="p-4 border-t border-white/10 bg-black/30 flex items-center justify-between">
            <span className="text-[11px] text-zinc-500 font-mono">Restricted Execution Guard Active</span>
            <button
              onClick={handleExecute}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-indigo-600 hover:from-emerald-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-lg shadow-emerald-600/20 transition-all flex items-center gap-2 active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>Run Code in Sandbox</span>
            </button>
          </div>
        </div>

        {/* Right Column: Console Guidance & Security Rules */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-6 rounded-3xl bg-[#0b0f19]/70 border border-white/10 glass-panel space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <TerminalIcon className="w-4 h-4 text-emerald-400" /> Output Stream & Console
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              When you click <strong className="text-white">Run Code</strong>, NOVA AI dispatches your script to the backend sandbox executor and streams output back to your active chat stream.
            </p>
            <div className="p-4 rounded-2xl bg-black/60 border border-white/5 font-mono text-xs text-emerald-400 space-y-1">
              <p className="text-zinc-500">$ nova-sandbox --lang={language}</p>
              <p>[SANDBOX] Initializing isolated process container...</p>
              <p>[SANDBOX] Ready for dispatch.</p>
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-indigo-950/20 border border-indigo-500/20 glass-panel space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-indigo-400" /> Security Policies Enforced
            </h3>
            <ul className="text-xs text-zinc-400 space-y-2">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" /> Dunder attribute inspection (__subclasses__) blocked
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" /> Process spawning and network sockets disabled
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" /> Hard 5.0-second execution time limit
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
