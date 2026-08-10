"use client";

import React, { useState } from "react";
import { BarChart3, Upload, FileSpreadsheet, Table, Sparkles, Loader2, Check } from "lucide-react";
import { streamChatResponse } from "@/lib/api/chat";
import { Message } from "@/types";
import { useToast } from "@/components/ui/Toast";

export function DataAnalysisWorkspace() {
  const toast = useToast();
  const [csvText, setCsvText] = useState<string>(
    `id,name,role,salary,department\n1,Alice,Engineer,125000,Engineering\n2,Bob,Product Manager,115000,Product\n3,Charlie,Data Scientist,130000,AI Engineering\n4,Diana,UX Designer,105000,Design\n5,Eve,DevOps Architect,140000,Infrastructure`
  );
  const [query, setQuery] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState("");

  const parsedData = React.useMemo(() => {
    try {
      const lines = csvText.trim().split("\n");
      if (lines.length === 0) return { headers: [], rows: [] };
      const headers = lines[0].split(",").map((h) => h.trim());
      const rows = lines.slice(1).map((line) => line.split(",").map((cell) => cell.trim()));
      return { headers, rows };
    } catch {
      return { headers: [], rows: [] };
    }
  }, [csvText]);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isAnalyzing || !csvText.trim()) return;

    setIsAnalyzing(true);
    setAnalysisResult("");

    try {
      let resultText = "";
      const promptContent = `Dataset Preview:\n\`\`\`csv\n${csvText.slice(0, 2500)}\n\`\`\`\nAnalysis Request: ${query.trim() || "Provide basic statistics, column summaries, and actionable data insights."}`;

      const messages: Message[] = [
        { id: "sys-data", role: "system", content: "You are the NOVA AI Data Analytics Specialist. Provide structured statistical analysis, dataset insights, and summary tables.", timestamp: new Date().toISOString() },
        { id: "user-data", role: "user", content: promptContent, timestamp: new Date().toISOString() }
      ];

      await streamChatResponse(messages, {
        mode: "data",
        model: "intelligence",
        onChunk: (chunk: string) => {
          resultText += chunk;
          setAnalysisResult(resultText);
        },
        onComplete: () => {
          setIsAnalyzing(false);
          toast.success("Dataset analysis completed.");
        },
        onError: (err: Error) => {
          setIsAnalyzing(false);
          toast.error(err.message || "Failed to analyze dataset.");
        }
      });
    } catch (err: any) {
      setIsAnalyzing(false);
      toast.error(err.message || "Analysis error.");
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      if (event.target?.result) {
        setCsvText(event.target.result as string);
        toast.success(`Loaded file: ${file.name}`);
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full space-y-6 overflow-y-auto">
      {/* Workspace Header */}
      <div className="border-b border-border pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">Data Analysis Workspace</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Inspect CSV/JSON datasets, calculate summary statistics, and query tabular data with AI.
            </p>
          </div>
        </div>

        <label className="flex items-center gap-2 px-4 py-2 rounded-xl border border-border bg-surface hover:bg-surface-hover text-xs font-semibold text-foreground transition-all cursor-pointer self-start sm:self-auto">
          <Upload className="w-4 h-4 text-amber-400" />
          <span>Upload CSV File</span>
          <input type="file" accept=".csv,.json,.txt" onChange={handleFileUpload} className="hidden" />
        </label>
      </div>

      {/* Dataset Grid & Input View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: CSV Input & Table Preview */}
        <div className="lg:col-span-7 flex flex-col space-y-4">
          <div className="p-4 rounded-2xl bg-surface border border-border glass-panel space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <FileSpreadsheet className="w-4 h-4 text-amber-400" />
                Raw CSV Dataset Input
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">
                {parsedData.rows.length} rows • {parsedData.headers.length} columns
              </span>
            </div>
            <textarea
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
              className="w-full h-44 p-3 rounded-xl bg-surface border border-border text-xs font-mono text-foreground focus:outline-none focus:border-amber-500/50 resize-none"
            />
          </div>

          {/* Interactive Data Table Preview */}
          {parsedData.headers.length > 0 && (
            <div className="p-4 rounded-2xl bg-surface border border-border glass-panel space-y-3 overflow-hidden">
              <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Table className="w-4 h-4 text-indigo-400" />
                Dataset Table Preview
              </span>
              <div className="max-h-56 overflow-auto border border-border/50 rounded-xl">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-surface-elevated text-muted-foreground border-b border-border sticky top-0">
                    <tr>
                      {parsedData.headers.map((h, i) => (
                        <th key={i} className="p-2.5 font-bold uppercase tracking-wider text-[10px]">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40 text-foreground/90">
                    {parsedData.rows.slice(0, 10).map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-surface-hover/50">
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="p-2.5 truncate max-w-[150px]">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Right: AI Data Analysis Query & Output */}
        <div className="lg:col-span-5 flex flex-col space-y-4">
          <form onSubmit={handleAnalyze} className="p-4 rounded-2xl bg-surface border border-border glass-panel space-y-3">
            <label className="text-xs font-bold text-foreground uppercase tracking-wider">Ask AI About Dataset</label>
            <input
              type="text"
              placeholder="e.g. What is the average salary by department?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-surface border border-border text-xs text-foreground focus:outline-none focus:border-amber-500"
            />
            <button
              type="submit"
              disabled={isAnalyzing || !csvText.trim()}
              className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analyzing Dataset...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Run Statistical Analysis</span>
                </>
              )}
            </button>
          </form>

          {/* Analysis Output Container */}
          {analysisResult && (
            <div className="p-5 rounded-2xl bg-surface border border-border glass-panel space-y-2 flex-1 min-h-[220px] overflow-y-auto">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block border-b border-border pb-2">
                Statistical Summary & Insights
              </span>
              <pre className="text-xs font-sans text-foreground/90 whitespace-pre-wrap leading-relaxed pt-2">{analysisResult}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
