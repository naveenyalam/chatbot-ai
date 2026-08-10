import React, { useState } from "react";
import { Search, Loader2, Sparkles, CheckCircle2, FileText, Globe, Layers, ArrowRight, Copy, Check } from "lucide-react";
import { streamChatResponse } from "@/lib/api/chat";
import { Message } from "@/types";
import { useToast } from "@/components/ui/Toast";

export function ResearchWorkspace() {
  const toast = useToast();
  const [query, setQuery] = useState("");
  const [isResearching, setIsResearching] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [report, setReport] = useState<string>("");
  const [copied, setCopied] = useState(false);

  const steps = [
    { label: "Search & Strategy", desc: "Generating research queries and vector parameters" },
    { label: "Retrieving Sources", desc: "Fetching document intelligence chunks and knowledge sources" },
    { label: "Cross-Information Analysis", desc: "Filtering noise, detecting patterns, and verifying claims" },
    { label: "Report Generation", desc: "Synthesizing structured findings with citations and limitations" },
  ];

  const handleStartResearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isResearching) return;

    setIsResearching(true);
    setCurrentStep(0);
    setReport("");

    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < 3) return prev + 1;
        clearInterval(stepInterval);
        return 3;
      });
    }, 1200);

    try {
      const messages: Message[] = [
        {
          id: "sys-research",
          role: "system",
          content: "You are the NOVA AI Deep Research Agent. Synthesize a comprehensive research report with: Executive Summary, Key Findings, Verified Sources/Claims, and Limitations/Nuances.",
          timestamp: new Date().toISOString()
        },
        {
          id: "user-research",
          role: "user",
          content: `Deep Research Topic: ${query.trim()}`,
          timestamp: new Date().toISOString()
        }
      ];

      await streamChatResponse(messages, {
        mode: "research",
        model: "intelligence",
        onChunk: (chunk: string) => {
          setReport((prev) => prev + chunk);
        },
        onComplete: () => {
          setIsResearching(false);
          toast.success("Deep research report synthesized successfully.");
        },
        onError: (err: Error) => {
          setIsResearching(false);
          toast.error(err.message || "Failed during research report synthesis.");
        }
      });
    } catch (err: any) {
      setIsResearching(false);
      toast.error(err.message || "Research failed.");
    }
  };

  const handleCopyReport = () => {
    navigator.clipboard.writeText(report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex-1 p-6 md:p-8 max-w-6xl mx-auto w-full space-y-6 overflow-y-auto">
      {/* Workspace Header */}
      <div className="border-b border-border pb-5">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <Search className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">Deep Research Workspace</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Conduct multi-step background research, source analysis, and structured report synthesis.
            </p>
          </div>
        </div>
      </div>

      {/* Research Input Card */}
      <form onSubmit={handleStartResearch} className="p-5 rounded-2xl bg-surface border border-border glass-panel space-y-4 shadow-sm">
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-foreground uppercase tracking-wider">Research Subject / Topic</label>
          <div className="relative">
            <input
              type="text"
              placeholder="e.g. Research quantum computing applications in pharmaceutical drug discovery..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full py-3 pl-4 pr-32 rounded-xl bg-surface border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-cyan-500 transition-all"
              disabled={isResearching}
              required
            />
            <button
              type="submit"
              disabled={isResearching || !query.trim()}
              className="absolute right-2 top-1.5 bottom-1.5 px-4 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold text-xs transition-all flex items-center gap-1.5 cursor-pointer"
            >
              {isResearching ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Researching...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Start Report</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Multi-Step Pipeline Indicator */}
      {(isResearching || report) && (
        <div className="p-5 rounded-2xl bg-surface border border-border glass-panel space-y-4">
          <h3 className="text-xs font-bold text-foreground uppercase tracking-wider">Research Execution Pipeline</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {steps.map((step, idx) => {
              const isDone = currentStep > idx || (!isResearching && report.length > 0);
              const isCurrent = currentStep === idx && isResearching;
              return (
                <div
                  key={step.label}
                  className={`p-3 rounded-xl border transition-all ${
                    isDone
                      ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                      : isCurrent
                      ? "bg-cyan-500/10 border-cyan-500/20 text-cyan-400 animate-pulse"
                      : "bg-surface/50 border-border text-muted-foreground"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : isCurrent ? (
                      <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                    ) : (
                      <span className="w-4 h-4 rounded-full border border-border text-[10px] font-bold flex items-center justify-center">
                        {idx + 1}
                      </span>
                    )}
                    <span className="text-xs font-bold truncate">{step.label}</span>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1 line-clamp-1">{step.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Generated Report Display */}
      {report && (
        <div className="p-6 rounded-2xl bg-surface border border-border glass-panel space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-4">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-400" />
              Synthesized Research Report
            </h3>
            <button
              onClick={handleCopyReport}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border bg-surface hover:bg-surface-hover text-xs font-semibold text-foreground transition-all cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-cyan-400" />}
              <span>{copied ? "Copied" : "Copy Report"}</span>
            </button>
          </div>
          <div className="font-sans text-xs text-foreground/90 leading-relaxed whitespace-pre-wrap">
            {report}
          </div>
        </div>
      )}
    </div>
  );
}
