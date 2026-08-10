"use client";

import React, { useState } from "react";
import {
  Bot,
  Play,
  Search,
  CheckCircle2,
  Clock,
  Sparkles,
  Terminal,
  FileSearch,
  Cpu,
  Layers,
  ArrowRight,
  RotateCcw,
} from "lucide-react";
import { ToolType } from "@/components/chat/ChatInput";

interface AgentWorkspaceProps {
  onLaunchAgentTask: (prompt: string, tool: ToolType) => void;
}

export function AgentWorkspace({ onLaunchAgentTask }: AgentWorkspaceProps) {
  const [selectedAgent, setSelectedAgent] = useState<ToolType>("task");
  const [agentPrompt, setAgentPrompt] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const agentsList = [
    {
      id: "task" as ToolType,
      name: "Autonomous Task Agent",
      desc: "Decomposes complex queries into multi-step execution plans and tool orchestrations.",
      icon: Bot,
      tools: ["Document RAG", "Calculator", "Code Sandbox", "Web Search"],
      badge: "Multi-Tool",
      accent: "from-indigo-500/20 to-purple-500/10 border-indigo-500/30 text-indigo-400",
    },
    {
      id: "research" as ToolType,
      name: "Deep Research Agent",
      desc: "Performs iterative sub-topic queries and multi-document synthesis.",
      icon: FileSearch,
      tools: ["Semantic Retrieval", "Web Citation Index", "Fact Verifier"],
      badge: "RAG Deep Dive",
      accent: "from-purple-500/20 to-pink-500/10 border-purple-500/30 text-purple-400",
    },
    {
      id: "code" as ToolType,
      name: "Sandboxed Developer Agent",
      desc: "Generates, executes, and validates Python/JavaScript code inside an isolated environment.",
      icon: Terminal,
      tools: ["Python 3.10 AST", "JS Engine", "Output Parser"],
      badge: "Restricted Sandbox",
      accent: "from-emerald-500/20 to-cyan-500/10 border-emerald-500/30 text-emerald-400",
    },
    {
      id: "web" as ToolType,
      name: "Real-Time Web Search Agent",
      desc: "Fetches live web information and domain intelligence.",
      icon: Search,
      tools: ["DuckDuckGo API", "URL Fetcher", "HTML Parser"],
      badge: "Live Web",
      accent: "from-cyan-500/20 to-blue-500/10 border-cyan-500/30 text-cyan-400",
    },
  ];

  const executionSteps = [
    { title: "Planning Phase", detail: "Decomposing task objective into sub-goals" },
    { title: "Knowledge Retrieval", detail: "Querying vector embeddings & document index" },
    { title: "Tool Execution", detail: "Invoking sandboxed execution engine" },
    { title: "Synthesizing Result", detail: "Verifying response grounding and generating final output" },
  ];

  const handleRunAgent = () => {
    if (!agentPrompt.trim()) return;
    setIsExecuting(true);
    setCurrentStepIndex(1);

    // Simulate visual timeline progression before launching live chat stream
    setTimeout(() => setCurrentStepIndex(2), 800);
    setTimeout(() => setCurrentStepIndex(3), 1600);
    setTimeout(() => {
      onLaunchAgentTask(agentPrompt, selectedAgent);
      setIsExecuting(false);
      setAgentPrompt("");
      setCurrentStepIndex(0);
    }, 2400);
  };

  const activeAgentInfo = agentsList.find((a) => a.id === selectedAgent) || agentsList[0];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 max-w-7xl mx-auto w-full select-none">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs font-semibold text-indigo-300">
          <Cpu className="w-3.5 h-3.5" /> ReAct Autonomous Workforce
        </div>
        <h1 className="text-3xl font-black text-white tracking-tight">
          AI Autonomous Agents
        </h1>
        <p className="text-sm text-zinc-400">
          Select an agent specialty, inspect available tools, and execute multi-step automated workflows.
        </p>
      </div>

      {/* Agents Selection Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {agentsList.map((ag) => {
          const Icon = ag.icon;
          const isSelected = selectedAgent === ag.id;

          return (
            <div
              key={ag.id}
              onClick={() => setSelectedAgent(ag.id)}
              className={`p-6 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between h-56 glass-panel ${
                isSelected
                  ? "bg-gradient-to-b " + ag.accent + " ring-1 ring-indigo-500/50 shadow-xl"
                  : "hover:bg-white/[0.04] border-white/5 opacity-80 hover:opacity-100"
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="p-2.5 rounded-xl bg-white/10 text-white">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="px-2 py-0.5 rounded-md bg-white/10 text-[10px] font-bold uppercase tracking-wider text-zinc-300">
                    {ag.badge}
                  </span>
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">{ag.name}</h3>
                  <p className="text-xs text-zinc-400 mt-1 line-clamp-2 leading-relaxed">
                    {ag.desc}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-1 pt-2 border-t border-white/10">
                {ag.tools.map((t, idx) => (
                  <span key={idx} className="text-[10px] px-2 py-0.5 rounded bg-black/40 text-zinc-300 border border-white/5">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Execution Launchpad Card */}
      <div className="p-6 md:p-8 rounded-3xl bg-[#0b0f19]/80 border border-white/10 glass-panel shadow-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-400">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">{activeAgentInfo.name} Launchpad</h2>
              <p className="text-xs text-zinc-400">Provide an objective for the agent to execute</p>
            </div>
          </div>
          <span className="text-xs px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
            Agent Status: Ready
          </span>
        </div>

        <div className="space-y-4">
          <textarea
            value={agentPrompt}
            onChange={(e) => setAgentPrompt(e.target.value)}
            disabled={isExecuting}
            placeholder={`Instruct ${activeAgentInfo.name} (e.g. "Research recent AI observability developments and execute code analysis to summarize metrics...")`}
            rows={3}
            className="w-full bg-zinc-950/60 border border-white/10 rounded-2xl p-4 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-indigo-500 transition-all resize-none"
          />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Multi-step ReAct reasoning loop enabled</span>
            </div>

            <button
              onClick={handleRunAgent}
              disabled={isExecuting || !agentPrompt.trim()}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/20 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {isExecuting ? (
                <>
                  <div className="w-4 h-4 border-2 border-t-white border-r-transparent border-b-transparent border-l-transparent animate-spin rounded-full" />
                  <span>Dispatching Agent...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Run Agent Execution</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Visual Execution Step Timeline */}
        {isExecuting && (
          <div className="pt-6 border-t border-white/10 space-y-4 animate-in fade-in">
            <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400">
              Live Agent Execution Pipeline
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              {executionSteps.map((step, idx) => {
                const isComplete = idx < currentStepIndex;
                const isCurrent = idx === currentStepIndex;

                return (
                  <div
                    key={idx}
                    className={`p-4 rounded-xl border text-left space-y-1 transition-all ${
                      isComplete
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                        : isCurrent
                        ? "bg-indigo-500/20 border-indigo-500/50 text-indigo-200 animate-pulse"
                        : "bg-white/[0.02] border-white/5 text-zinc-500"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs font-bold">
                      <span>Step {idx + 1}</span>
                      {isComplete ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : isCurrent ? (
                        <Clock className="w-4 h-4 text-indigo-400 animate-spin" />
                      ) : null}
                    </div>
                    <p className="text-xs font-semibold">{step.title}</p>
                    <p className="text-[10px] text-zinc-400">{step.detail}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
