import React, { useState, useRef, useEffect } from "react";
import { Menu, Search, Sun, Moon, Sparkles, ChevronDown, Zap, Lightbulb, Share2, SlidersHorizontal, Loader2, Download, FileText, Code2, Bot, BarChart3, Layers, MessageSquare, PenTool } from "lucide-react";
import { useApp } from "@/components/providers/ThemeProvider";
import { cn } from "@/lib/utils";
import { WorkspaceView } from "@/types";
import { useToast } from "@/components/ui/Toast";
import { NotificationCenter } from "@/components/ui/NotificationCenter";

interface HeaderProps {
  onOpenSidebar: () => void;
  onOpenSettings: () => void;
  onOpenCommandPalette: () => void;
  chatTitle: string | null;
  selectedModel: string;
  onSelectModel: (model: string) => void;
  activeView: WorkspaceView;
  onChangeView?: (view: WorkspaceView) => void;
  onExportChat?: (format: "md" | "json" | "txt") => void;
}

export function Header({
  onOpenSidebar,
  onOpenSettings,
  onOpenCommandPalette,
  chatTitle,
  selectedModel,
  onSelectModel,
  activeView,
  onChangeView,
  onExportChat,
}: HeaderProps) {
  const { theme, setTheme } = useApp();
  const toast = useToast();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isWorkspaceDropdownOpen, setIsWorkspaceDropdownOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isApplyingModel, setIsApplyingModel] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const workspaceDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsApplyingModel(true);
    const timer = setTimeout(() => {
      setIsApplyingModel(false);
    }, 450);
    return () => clearTimeout(timer);
  }, [selectedModel]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false);
      }
      if (workspaceDropdownRef.current && !workspaceDropdownRef.current.contains(e.target as Node)) {
        setIsWorkspaceDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const models = [
    {
      id: "intelligence",
      name: "NOVA Intelligence 3.5",
      desc: "Balanced deep multi-modal reasoning & prose synthesis",
      icon: Sparkles,
      iconColor: "text-indigo-600 dark:text-indigo-400",
    },
    {
      id: "fast",
      name: "NOVA Fast Latency",
      desc: "Ultra-low TTFT optimized for real-time streaming",
      icon: Zap,
      iconColor: "text-amber-600 dark:text-amber-400",
    },
    {
      id: "reason",
      name: "NOVA Reason DeepThink",
      desc: "Collapsible step-by-step chain of thought reasoning",
      icon: Lightbulb,
      iconColor: "text-cyan-600 dark:text-cyan-400",
    },
  ] as const;

  const workspaces = [
    { id: "chat" as WorkspaceView, name: "General AI", desc: "General multi-modal chat & reasoning", icon: MessageSquare },
    { id: "research" as WorkspaceView, name: "Research", desc: "Multi-source research & synthesis", icon: Search },
    { id: "writing" as WorkspaceView, name: "Writing", desc: "Draft, rewrite, summarize & polish content", icon: PenTool },
    { id: "code" as WorkspaceView, name: "Coding", desc: "Sandboxed execution & debugging", icon: Code2 },
    { id: "documents" as WorkspaceView, name: "Documents", desc: "Knowledge retrieval & file RAG", icon: FileText },
    { id: "data" as WorkspaceView, name: "Data Analysis", desc: "CSV/JSON dataset summary & stats", icon: BarChart3 },
    { id: "agents" as WorkspaceView, name: "Agent Workspace", desc: "Autonomous tool execution pipelines", icon: Bot },
  ] as const;

  const currentModel = models.find((m) => m.id === selectedModel) || models[0];
  const ActiveModelIcon = currentModel.icon;
  const currentWorkspace = workspaces.find((w) => w.id === activeView) || workspaces[0];
  const CurrentWorkspaceIcon = currentWorkspace.icon;

  const getWorkspaceTitle = () => {
    switch (activeView) {
      case "dashboard": return "Platform Overview";
      case "documents": return "Knowledge Retrieval Base";
      case "agents": return "Autonomous AI Agents";
      case "code": return "Developer Sandbox";
      case "research": return "Research Mode Workspace";
      case "writing": return "Writing Assistant Mode";
      case "data": return "Data Analysis Workspace";
      case "prompts": return "Prompt Library";
      case "templates": return "Chat Templates";
      case "saved": return "Saved AI Responses";
      case "settings": return "System Settings";
      default: return chatTitle || "New Conversation";
    }
  };

  return (
    <header className="h-16 px-4 md:px-6 border-b border-border flex items-center justify-between bg-surface/90 backdrop-blur-xl sticky top-0 z-30 select-none glass-panel">
      {/* Left side: Hamburger + Workspace Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenSidebar}
          className="md:hidden p-2 rounded-xl hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-all cursor-pointer"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <h1 className="text-xs md:text-sm font-bold text-foreground truncate max-w-[120px] sm:max-w-[200px] md:max-w-[280px]">
          {getWorkspaceTitle()}
        </h1>
      </div>

      {/* Center: AI Workspace Switcher & Model Selector Dropdowns */}
      <div className="flex items-center gap-2">
        {/* Workspace Selector */}
        <div className="relative" ref={workspaceDropdownRef}>
          <button
            onClick={() => setIsWorkspaceDropdownOpen(!isWorkspaceDropdownOpen)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border hover:border-indigo-500/40 bg-surface hover:bg-surface-hover text-xs font-semibold text-foreground shadow-sm transition-all cursor-pointer"
            aria-haspopup="listbox"
            aria-expanded={isWorkspaceDropdownOpen}
            aria-label="Select AI Workspace Mode"
          >
            <CurrentWorkspaceIcon className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden md:inline">{currentWorkspace.name}</span>
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
          </button>

          {isWorkspaceDropdownOpen && (
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 w-72 bg-surface-elevated border border-border rounded-2xl shadow-2xl glass-panel p-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="px-3 py-1.5 text-[9px] font-bold text-muted-foreground tracking-wider uppercase border-b border-border mb-1.5">
                AI Workspace Mode Switcher
              </div>
              <div className="space-y-0.5">
                {workspaces.map((ws) => {
                  const Icon = ws.icon;
                  const isSelected = activeView === ws.id;
                  return (
                    <button
                      key={ws.id}
                      onClick={() => {
                        onChangeView?.(ws.id);
                        setIsWorkspaceDropdownOpen(false);
                      }}
                      className={cn(
                        "w-full flex items-start gap-3 p-2 rounded-xl text-left transition-all border border-transparent cursor-pointer",
                        isSelected
                          ? "bg-indigo-600/10 border-indigo-500/20 text-indigo-600 dark:text-indigo-300 font-semibold"
                          : "hover:bg-surface-hover text-muted-foreground hover:text-foreground"
                      )}
                    >
                      <div className="p-1.5 rounded-lg border border-border bg-surface/50 mt-0.5">
                        <Icon className="w-4 h-4 text-indigo-400" />
                      </div>
                      <div className="flex-grow min-w-0">
                        <p className="text-xs font-semibold truncate">{ws.name}</p>
                        <p className="text-[10px] text-muted-foreground leading-normal mt-0.5">{ws.desc}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Model Selector Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-border hover:border-indigo-500/40 bg-surface hover:bg-surface-hover text-xs font-semibold text-foreground shadow-sm transition-all cursor-pointer"
            aria-haspopup="listbox"
            aria-expanded={isDropdownOpen}
            aria-label="Select AI Model"
          >
            {isApplyingModel ? (
              <Loader2 className="w-3.5 h-3.5 text-indigo-500 dark:text-indigo-400 animate-spin" />
            ) : (
              <ActiveModelIcon className={cn("w-3.5 h-3.5", currentModel.iconColor)} />
            )}
            <span className="hidden lg:inline">{isApplyingModel ? "Applying Engine..." : currentModel.name}</span>
            <span className="lg:hidden">{isApplyingModel ? "Applying..." : currentModel.name.split(" ")[0]}</span>
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
          </button>

          {isDropdownOpen && (
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 w-72 bg-surface-elevated border border-border rounded-2xl shadow-2xl glass-panel p-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="px-3 py-1.5 text-[9px] font-bold text-muted-foreground tracking-wider uppercase border-b border-border mb-1.5">
                Select AI Model Intelligence Engine
              </div>
              <div className="space-y-0.5">
                {models.map((model) => {
                  const Icon = model.icon;
                  const isSelected = selectedModel === model.id;
                  return (
                    <button
                      key={model.id}
                      onClick={() => {
                        onSelectModel(model.id);
                        setIsDropdownOpen(false);
                      }}
                      className={cn(
                        "w-full flex items-start gap-3 p-2.5 rounded-xl text-left transition-all border border-transparent cursor-pointer",
                        isSelected
                          ? "bg-indigo-600/10 border-indigo-500/20 text-indigo-600 dark:text-indigo-300"
                          : "hover:bg-surface-hover text-muted-foreground hover:text-foreground"
                      )}
                    >
                      <div className="p-1.5 rounded-lg border border-border bg-surface/50 mt-0.5">
                        <Icon className={cn("w-4 h-4", model.iconColor)} />
                      </div>
                      <div className="flex-grow min-w-0">
                        <p className="text-xs font-semibold truncate">{model.name}</p>
                        <p className="text-[10px] text-muted-foreground leading-normal mt-0.5">{model.desc}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right side: Actions & Notifications */}
      <div className="flex items-center gap-1.5">
        {activeView === "chat" && chatTitle && (
          <div className="relative">
            <button
              onClick={() => setIsExportOpen(!isExportOpen)}
              className="p-2 rounded-xl hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-all cursor-pointer"
              title="Export Conversation"
            >
              <Download className="w-4 h-4 text-indigo-400" />
            </button>

            {isExportOpen && (
              <div className="absolute right-0 top-full mt-2 w-44 bg-surface-elevated border border-border rounded-xl shadow-2xl glass-panel p-1 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
                <div className="px-2.5 py-1 text-[9px] font-bold text-muted-foreground tracking-wider uppercase border-b border-border mb-1">
                  Export Conversation
                </div>
                <button
                  onClick={() => {
                    onExportChat?.("md");
                    setIsExportOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-surface-hover text-foreground flex items-center gap-2"
                >
                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Markdown (.md)</span>
                </button>
                <button
                  onClick={() => {
                    onExportChat?.("json");
                    setIsExportOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-surface-hover text-foreground flex items-center gap-2"
                >
                  <Code2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>JSON (.json)</span>
                </button>
                <button
                  onClick={() => {
                    onExportChat?.("txt");
                    setIsExportOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-surface-hover text-foreground flex items-center gap-2"
                >
                  <FileText className="w-3.5 h-3.5 text-amber-400" />
                  <span>Plain Text (.txt)</span>
                </button>
              </div>
            )}
          </div>
        )}

        <NotificationCenter />

        <button
          onClick={() => {
            if (navigator.share) {
              navigator.share({ title: getWorkspaceTitle(), url: window.location.href }).catch(() => {});
            } else {
              navigator.clipboard.writeText(window.location.href);
              toast.success("Workspace URL copied to clipboard.");
            }
          }}
          className="p-2 rounded-xl hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-all hidden sm:block cursor-pointer"
          title="Share workspace link"
        >
          <Share2 className="w-4 h-4" />
        </button>

        <button
          onClick={onOpenCommandPalette}
          className="p-2 rounded-xl hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-all cursor-pointer"
          title="Command Palette (Ctrl+K)"
        >
          <Search className="w-4 h-4" />
        </button>

        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="p-2 rounded-xl hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-all cursor-pointer"
          title="Toggle color theme"
        >
          {theme === "dark" ? <Sun className="w-4 h-4 text-amber-500" /> : <Moon className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />}
        </button>

        <button
          onClick={onOpenSettings}
          className="p-2 rounded-xl hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-all cursor-pointer"
          title="Settings"
        >
          <SlidersHorizontal className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
