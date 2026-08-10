"use client";

import React, { useEffect, useState, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Plus,
  Settings,
  Sun,
  Moon,
  HelpCircle,
  X,
  Sparkles,
  FileText,
  Bot,
  Code2,
  LayoutDashboard,
  MessageSquare,
} from "lucide-react";
import { useApp } from "@/components/providers/ThemeProvider";
import { Chat } from "@/types";

import { unifiedSearch, UnifiedSearchResults } from "@/lib/api/workspace";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectAction: (action: string) => void;
  chats?: Chat[];
  onSelectChat?: (id: string) => void;
}

export function CommandPalette({
  isOpen,
  onClose,
  onSelectAction,
  chats = [],
  onSelectChat,
}: CommandPaletteProps) {
  const { theme, setTheme, settings } = useApp();
  const [search, setSearch] = useState("");
  const [unifiedResults, setUnifiedResults] = useState<UnifiedSearchResults>({
    conversations: [],
    documents: [],
    prompts: [],
    saved_responses: [],
  });
  const [isSearchingServer, setIsSearchingServer] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const animate = settings.animationsEnabled;

  // Unified server search with AbortController
  useEffect(() => {
    if (!search || search.trim().length < 2) {
      setUnifiedResults({ conversations: [], documents: [], prompts: [], saved_responses: [] });
      setIsSearchingServer(false);
      return;
    }

    const controller = new AbortController();
    setIsSearchingServer(true);

    const timer = setTimeout(async () => {
      try {
        const results = await unifiedSearch(search, controller.signal);
        setUnifiedResults(results);
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.error("Unified search failed:", err);
        }
      } finally {
        setIsSearchingServer(false);
      }
    }, 250);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [search]);

  const items = useMemo(() => [
    {
      id: "new-chat",
      name: "New Conversation",
      icon: Plus,
      description: "Start a fresh AI chat thread",
      action: () => onSelectAction("new-chat"),
    },
    {
      id: "documents",
      name: "Knowledge Base & RAG",
      icon: FileText,
      description: "Upload and query PDF/text documents",
      action: () => onSelectAction("documents"),
    },
    {
      id: "collections",
      name: "Knowledge Collections",
      icon: FileText,
      description: "Organize documents into subject domains",
      action: () => onSelectAction("collections"),
    },
    {
      id: "research",
      name: "Research Workspace",
      icon: Search,
      description: "Multi-stage source synthesis and report generation",
      action: () => onSelectAction("research"),
    },
    {
      id: "agents",
      name: "AI Autonomous Agents",
      icon: Bot,
      description: "Launch multi-step tool execution pipelines",
      action: () => onSelectAction("agents"),
    },
    {
      id: "code",
      name: "Developer Code Sandbox",
      icon: Code2,
      description: "Execute sandboxed Python & JavaScript code",
      action: () => onSelectAction("code"),
    },
    {
      id: "data",
      name: "Data Analysis Workspace",
      icon: LayoutDashboard,
      description: "Inspect CSV/JSON datasets and calculate statistics",
      action: () => onSelectAction("data"),
    },
    {
      id: "prompts",
      name: "Prompt Library",
      icon: Sparkles,
      description: "Access saved system prompts and custom templates",
      action: () => onSelectAction("prompts"),
    },
    {
      id: "templates",
      name: "Interactive Chat Templates",
      icon: FileText,
      description: "Use prompt templates with variable input fields",
      action: () => onSelectAction("templates"),
    },
    {
      id: "saved",
      name: "Saved AI Responses",
      icon: Sparkles,
      description: "View bookmarked AI answers and code snippets",
      action: () => onSelectAction("saved"),
    },
    {
      id: "settings",
      name: "System Settings",
      icon: Settings,
      description: "Manage preferences and data controls",
      action: () => onSelectAction("settings"),
    },
    {
      id: "theme",
      name: `Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`,
      icon: theme === "dark" ? Sun : Moon,
      description: "Toggle interface light or dark appearance",
      action: () => {
        setTheme(theme === "dark" ? "light" : "dark");
        onClose();
      },
    },
    {
      id: "shortcuts",
      name: "View Keyboard Shortcuts",
      icon: HelpCircle,
      description: "Display hotkeys and system commands",
      action: () => onSelectAction("shortcuts"),
    },
  ], [theme, setTheme, onSelectAction, onClose]);

  const filteredItems = useMemo(() => {
    const matchedActions = items.filter(
      (item) =>
        item.name.toLowerCase().includes(search.toLowerCase()) ||
        item.description.toLowerCase().includes(search.toLowerCase())
    );

    const localChats = chats
      .filter((chat) => chat.title.toLowerCase().includes(search.toLowerCase()))
      .slice(0, 5)
      .map((chat) => ({
        id: `chat-${chat.id}`,
        name: chat.title,
        icon: MessageSquare,
        description: "Conversation",
        action: () => {
          onSelectChat?.(chat.id);
          onSelectAction("chat");
          onClose();
        },
      }));

    const docItems = (unifiedResults.documents || []).slice(0, 4).map((d) => ({
      id: `doc-${d.id}`,
      name: d.name,
      icon: FileText,
      description: "Document (RAG Base)",
      action: () => {
        onSelectAction("documents");
        onClose();
      },
    }));

    const promptItems = (unifiedResults.prompts || []).slice(0, 4).map((p) => ({
      id: `prompt-${p.id}`,
      name: p.title,
      icon: Sparkles,
      description: "Prompt Library Item",
      action: () => {
        onSelectAction("prompts");
        onClose();
      },
    }));

    const savedItems = (unifiedResults.saved_responses || []).slice(0, 4).map((s) => ({
      id: `saved-${s.id}`,
      name: s.title,
      icon: Sparkles,
      description: "Saved AI Response",
      action: () => {
        onSelectAction("saved");
        onClose();
      },
    }));

    return [...matchedActions, ...localChats, ...docItems, ...promptItems, ...savedItems];
  }, [search, chats, unifiedResults, onSelectChat, onSelectAction, onClose, items]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        inputRef.current?.focus();
        setSearch("");
        setSelectedIndex(0);
      }, 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
    }
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, [isOpen, onClose]);

  // Safeguard selectedIndex range
  useEffect(() => {
    if (filteredItems.length > 0 && selectedIndex >= filteredItems.length) {
      setSelectedIndex(filteredItems.length - 1);
    }
  }, [filteredItems, selectedIndex]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredItems.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filteredItems.length - 1
        );
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filteredItems[selectedIndex]) {
          filteredItems[selectedIndex].action();
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filteredItems, selectedIndex, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-black/60 dark:bg-black/75 backdrop-blur-md"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            ref={containerRef}
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            className="w-full max-w-xl bg-surface-primary border border-border-subtle rounded-3xl shadow-2xl overflow-hidden glass-panel"
          >
            {/* Search Input Bar */}
            <div className="flex items-center px-5 border-b border-border-subtle">
              <Search className="w-5 h-5 text-text-muted mr-3" />
              <input
                ref={inputRef}
                type="text"
                placeholder="Type a command or search workspace..."
                className="w-full py-4.5 bg-transparent outline-none border-none text-text-primary placeholder:text-text-muted/60 text-sm font-medium"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setSelectedIndex(0);
                }}
              />
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="p-1 rounded-full hover:bg-surface-secondary text-text-muted cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
              <div className="hidden sm:flex items-center gap-1 ml-2 border border-border-subtle bg-surface-secondary/40 rounded-lg px-2 py-0.5 text-[10px] font-mono text-text-muted">
                ESC
              </div>
            </div>

            {/* Suggestions / Results */}
            <div className="max-h-80 overflow-y-auto p-2">
              {filteredItems.length > 0 ? (
                <div className="space-y-1">
                  <div className="px-3 py-1.5 text-[10px] font-bold text-text-muted tracking-wider uppercase flex items-center">
                    <Sparkles className="w-3.5 h-3.5 mr-1 text-accent" />
                    NOVA AI Commands
                  </div>
                  {filteredItems.map((item, idx) => {
                    const Icon = item.icon;
                    const isSelected = idx === selectedIndex;
                    return (
                      <button
                        key={item.id}
                        onClick={item.action}
                        onMouseEnter={() => setSelectedIndex(idx)}
                        className={`w-full flex items-center px-4 py-3 rounded-2xl transition-all duration-150 text-left cursor-pointer ${
                          isSelected
                            ? "bg-accent text-white shadow-lg shadow-accent/25"
                            : "text-text-primary hover:bg-surface-secondary"
                        }`}
                      >
                        <Icon
                          className={`w-5 h-5 mr-3.5 flex-shrink-0 ${
                            isSelected ? "text-white" : "text-text-muted"
                          }`}
                        />
                        <div className="flex-grow">
                          <p className="text-xs font-bold">{item.name}</p>
                          <p
                            className={`text-[11px] ${
                              isSelected ? "text-white/80" : "text-text-muted"
                            }`}
                          >
                            {item.description}
                          </p>
                        </div>
                        {isSelected && (
                          <div className="text-[10px] border border-white/20 bg-white/10 rounded-md px-2 py-0.5 font-mono">
                            Enter
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="py-12 text-center text-text-muted text-xs italic">
                  No commands found matching &ldquo;{search}&rdquo;
                </div>
              )}
            </div>

            {/* Footer Help */}
            <div className="flex items-center justify-between px-5 py-3 border-t border-border-subtle bg-surface-secondary/40 text-[11px] text-text-muted font-medium">
              <div className="flex items-center gap-4">
                <span>↑↓ navigate</span>
                <span>Enter select</span>
              </div>
              <div>NOVA AI Platform OS</div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
