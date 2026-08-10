"use client";

import React, { useState } from "react";
import { Code2, Play, Copy, Check, Terminal, FileCode, Sparkles, Loader2, RotateCcw, Bug, Cpu } from "lucide-react";
import { streamChatResponse } from "@/lib/api/chat";
import { Message } from "@/types";
import { useToast } from "@/components/ui/Toast";

export function CodingWorkspace() {
  const toast = useToast();
  const [code, setCode] = useState<string>(
    `# Python Sandbox Algorithm Example\ndef fibonacci_sequence(n: int):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    seq = [0, 1]\n    for i in range(2, n):\n        seq.append(seq[-1] + seq[-2])\n    return seq\n\nprint("Fibonacci sequence:", fibonacci_sequence(10))`
  );
  const [language, setLanguage] = useState("python");
  const [prompt, setPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [output, setOutput] = useState<string>("");
  const [copied, setCopied] = useState(false);

  const handleGenerateOrRefactor = async (mode: "generate" | "explain" | "debug" | "optimize") => {
    if (isGenerating) return;
    setIsGenerating(true);
    let userPrompt = "";

    if (mode === "generate") {
      if (!prompt.trim()) {
        toast.error("Please enter instructions for code generation.");
        setIsGenerating(false);
        return;
      }
      userPrompt = `Write clean ${language} code for: ${prompt.trim()}`;
    } else if (mode === "explain") {
      userPrompt = `Explain step-by-step what this ${language} code does:\n\`\`\`${language}\n${code}\n\`\`\``;
    } else if (mode === "debug") {
      userPrompt = `Identify potential bugs, edge cases, and runtime issues in this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\``;
    } else if (mode === "optimize") {
      userPrompt = `Refactor and optimize performance for this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\``;
    }

    try {
      let aiOutput = "";
      const messages: Message[] = [
        { id: "sys-code", role: "system", content: "You are the NOVA AI Senior Software Architect. Provide production-grade code snippets and clear explanations.", timestamp: new Date().toISOString() },
        { id: "user-code", role: "user", content: userPrompt, timestamp: new Date().toISOString() }
      ];

      await streamChatResponse(messages, {
        mode: "code",
        model: "intelligence",
        onChunk: (chunk: string) => {
          aiOutput += chunk;
          setOutput(aiOutput);
        },
        onComplete: () => {
          setIsGenerating(false);
          toast.success(`Code ${mode} complete.`);
        },
        onError: (err: Error) => {
          setIsGenerating(false);
          toast.error(err.message || "Failed to process code request.");
        }
      });
    } catch (err: any) {
      setIsGenerating(false);
      toast.error(err.message || "Execution error.");
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full space-y-6 overflow-y-auto">
      {/* Header */}
      <div className="border-b border-border pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Code2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">Developer Sandbox Workspace</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Refactor, debug, optimize, and generate code with AI developer tools.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-surface border border-border text-xs text-foreground font-mono focus:outline-none"
          >
            <option value="python">Python</option>
            <option value="typescript">TypeScript</option>
            <option value="javascript">JavaScript</option>
            <option value="rust">Rust</option>
            <option value="go">Go</option>
            <option value="html">HTML/CSS</option>
          </select>
          <button
            onClick={handleCopyCode}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border bg-surface hover:bg-surface-hover text-xs font-semibold text-foreground transition-all cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-emerald-400" />}
            <span>{copied ? "Copied" : "Copy Code"}</span>
          </button>
        </div>
      </div>

      {/* Main Workspace Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left / Code Editor Area */}
        <div className="lg:col-span-7 flex flex-col space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
              <FileCode className="w-4 h-4 text-emerald-400" />
              Source Editor ({language})
            </span>
            <span className="text-[10px] text-muted-foreground font-mono">UTF-8 • Lines: {code.split("\n").length}</span>
          </div>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full h-96 p-4 rounded-2xl bg-surface/90 border border-border text-xs font-mono text-foreground focus:outline-none focus:border-emerald-500/50 resize-none shadow-inner leading-relaxed"
            placeholder="Type or paste your code snippet here..."
          />
        </div>

        {/* Right / AI Action & Output Panel */}
        <div className="lg:col-span-5 flex flex-col space-y-4">
          <div className="p-4 rounded-2xl bg-surface border border-border glass-panel space-y-3">
            <label className="text-xs font-bold text-foreground uppercase tracking-wider">AI Developer Action</label>
            <input
              type="text"
              placeholder="Prompt AI to generate code..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-surface border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-emerald-500"
            />
            <div className="grid grid-cols-2 gap-2 pt-1">
              <button
                onClick={() => handleGenerateOrRefactor("generate")}
                disabled={isGenerating || !prompt.trim()}
                className="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer"
              >
                {isGenerating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                <span>Generate</span>
              </button>
              <button
                onClick={() => handleGenerateOrRefactor("optimize")}
                disabled={isGenerating}
                className="px-3 py-2 rounded-xl border border-border bg-surface hover:bg-surface-hover text-foreground font-semibold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                <span>Optimize</span>
              </button>
              <button
                onClick={() => handleGenerateOrRefactor("explain")}
                disabled={isGenerating}
                className="px-3 py-2 rounded-xl border border-border bg-surface hover:bg-surface-hover text-foreground font-semibold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span>Explain</span>
              </button>
              <button
                onClick={() => handleGenerateOrRefactor("debug")}
                disabled={isGenerating}
                className="px-3 py-2 rounded-xl border border-border bg-surface hover:bg-surface-hover text-foreground font-semibold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Bug className="w-3.5 h-3.5 text-amber-400" />
                <span>Debug</span>
              </button>
            </div>
          </div>

          {/* AI Output Terminal Display */}
          {output && (
            <div className="p-4 rounded-2xl bg-surface border border-border glass-panel space-y-2 flex-1 min-h-[200px] overflow-y-auto">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">AI Output / Analysis</span>
              <pre className="text-xs font-mono text-foreground/90 whitespace-pre-wrap leading-relaxed">{output}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
