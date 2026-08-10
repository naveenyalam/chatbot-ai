"use client";

import React from "react";
import {
  MessageSquare,
  FileText,
  Bot,
  Code2,
  Plus,
  Sparkles,
  TrendingUp,
  Zap,
  Shield,
  Activity,
  ArrowUpRight,
  FolderOpen,
} from "lucide-react";
import { User, Chat } from "@/types";
import { DocumentResponse } from "@/lib/api/documents";

interface DashboardOverviewProps {
  user: User | null;
  chats: Chat[];
  documents: DocumentResponse[];
  onNewChat: () => void;
  onOpenDocuments: () => void;
  onOpenAgents: () => void;
  onOpenCode: () => void;
}

export function DashboardOverview({
  user,
  chats,
  documents,
  onNewChat,
  onOpenDocuments,
  onOpenAgents,
  onOpenCode,
}: DashboardOverviewProps) {
  const userName = user?.name ? user.name.split(" ")[0] : "Architect";

  // Calculate live statistics from actual state
  const totalConversations = chats.length;
  const totalDocuments = documents.length;
  const readyDocuments = documents.filter((d) => d.status === "indexed").length;
  const totalTokensEst = chats.reduce((acc, c) => acc + (c.messages.length * 140), 0);

  const quickActions = [
    {
      title: "New Conversation",
      desc: "Start an interactive context-aware session",
      icon: MessageSquare,
      color: "from-indigo-500/20 to-indigo-600/10 border-indigo-500/30 text-indigo-400",
      action: onNewChat,
    },
    {
      title: "Upload Documents",
      desc: "Ingest PDFs or text into RAG knowledge base",
      icon: FileText,
      color: "from-purple-500/20 to-purple-600/10 border-purple-500/30 text-purple-400",
      action: onOpenDocuments,
    },
    {
      title: "Launch Autonomous Agent",
      desc: "Orchestrate multi-step tool execution",
      icon: Bot,
      color: "from-cyan-500/20 to-cyan-600/10 border-cyan-500/30 text-cyan-400",
      action: onOpenAgents,
    },
    {
      title: "Developer Sandbox",
      desc: "Compile Python & JS in secure micro-sandbox",
      icon: Code2,
      color: "from-emerald-500/20 to-emerald-600/10 border-emerald-500/30 text-emerald-400",
      action: onOpenCode,
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 max-w-7xl mx-auto w-full select-none">
      {/* Hero Greeting Banner */}
      <div className="relative overflow-hidden rounded-3xl p-8 md:p-10 border border-border bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-surface-elevated backdrop-blur-xl shadow-2xl">
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs font-semibold text-indigo-500 dark:text-indigo-300">
            <Sparkles className="w-3.5 h-3.5" /> NOVA AI OS v1.3.0 Ready
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-foreground tracking-tight">
            Good day, <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-500 dark:from-indigo-400 dark:via-purple-400 dark:to-cyan-400">{userName}</span>
          </h1>
          <p className="text-sm md:text-base text-muted-foreground max-w-2xl">
            What would you like to accomplish today? Choose a quick action below or start a new conversation.
          </p>
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Zap className="w-4 h-4 text-indigo-500 dark:text-indigo-400" /> Quick Workspaces
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                onClick={item.action}
                className={`p-6 rounded-2xl bg-gradient-to-br ${item.color} border hover:scale-[1.02] active:scale-[0.99] transition-all text-left group flex flex-col justify-between h-44 shadow-lg cursor-pointer`}
              >
                <div className="flex items-center justify-between">
                  <div className="p-3 rounded-xl bg-surface/40 backdrop-blur-md">
                    <Icon className="w-6 h-6" />
                  </div>
                  <ArrowUpRight className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity text-foreground" />
                </div>
                <div>
                  <h3 className="font-bold text-foreground text-base group-hover:text-indigo-400 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                    {item.desc}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Analytics & Platform Stats */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Activity className="w-4 h-4 text-indigo-500 dark:text-indigo-400" /> Platform Telemetry & Usage
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-6 rounded-2xl bg-surface-elevated border border-border backdrop-blur-xl">
            <div className="flex items-center justify-between text-muted-foreground text-xs font-medium">
              <span>Active Chats</span>
              <MessageSquare className="w-4 h-4 text-indigo-500 dark:text-indigo-400" />
            </div>
            <p className="text-3xl font-black text-foreground mt-3">{totalConversations}</p>
            <p className="text-[11px] text-muted-foreground mt-1">Saved conversation histories</p>
          </div>

          <div className="p-6 rounded-2xl bg-surface-elevated border border-border backdrop-blur-xl">
            <div className="flex items-center justify-between text-muted-foreground text-xs font-medium">
              <span>Knowledge Library</span>
              <FolderOpen className="w-4 h-4 text-purple-500 dark:text-purple-400" />
            </div>
            <p className="text-3xl font-black text-foreground mt-3">{totalDocuments}</p>
            <p className="text-[11px] text-muted-foreground mt-1">{readyDocuments} RAG chunks active</p>
          </div>

          <div className="p-6 rounded-2xl bg-surface-elevated border border-border backdrop-blur-xl">
            <div className="flex items-center justify-between text-muted-foreground text-xs font-medium">
              <span>Est. Token Ingestion</span>
              <TrendingUp className="w-4 h-4 text-cyan-500 dark:text-cyan-400" />
            </div>
            <p className="text-3xl font-black text-foreground mt-3">{totalTokensEst.toLocaleString()}</p>
            <p className="text-[11px] text-muted-foreground mt-1">~${(totalTokensEst * 0.000002).toFixed(4)} est. model cost</p>
          </div>

          <div className="p-6 rounded-2xl bg-surface-elevated border border-border backdrop-blur-xl">
            <div className="flex items-center justify-between text-muted-foreground text-xs font-medium">
              <span>Budget & Quota Status</span>
              <Shield className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            </div>
            <p className="text-3xl font-black text-emerald-500 dark:text-emerald-400 mt-3">Healthy</p>
            <p className="text-[11px] text-muted-foreground mt-1">Enforcing 1,000 API req/day cap</p>
          </div>
        </div>
      </div>
    </div>
  );
}
