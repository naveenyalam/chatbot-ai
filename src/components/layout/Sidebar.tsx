"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Plus,
  MessageSquare,
  MoreVertical,
  Edit2,
  Copy,
  Trash2,
  Settings as SettingsIcon,
  LogOut,
  ChevronUp,
  Keyboard,
  X,
  Check,
  Search,
  LayoutDashboard,
  FileText,
  Bot,
  Code2,
  Sparkles,
  Sun,
  Moon,
} from "lucide-react";
import {
  FolderKanban,
  Search as SearchIcon,
  BarChart3,
  BookOpen,
  Bookmark,
  FileCode2,
  HelpCircle
} from "lucide-react";
import { Chat, User, WorkspaceView } from "@/types";
export type { WorkspaceView } from "@/types";
import { useApp } from "@/components/providers/ThemeProvider";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  chats: Chat[];
  activeChatId: string | null;
  activeView: WorkspaceView;
  onChangeView: (view: WorkspaceView) => void;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string) => void;
  onRenameChat: (id: string, newTitle: string) => void;
  onDuplicateChat: (id: string) => void;
  onOpenSettings: () => void;
  onOpenCommandPalette: () => void;
  user: User | null;
  onSignOut: () => void;
}


export function Sidebar({
  isOpen,
  onClose,
  chats,
  activeChatId,
  activeView,
  onChangeView,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat,
  onDuplicateChat,
  onOpenSettings,
  onOpenCommandPalette,
  user,
  onSignOut,
}: SidebarProps) {
  const { theme, setTheme } = useApp();
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close menus on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (activeMenuId && !target.closest(".chat-menu-container")) {
        setActiveMenuId(null);
        setConfirmDeleteId(null);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(target)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [activeMenuId]);

  const handleStartRename = (chat: Chat, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingChatId(chat.id);
    setEditTitle(chat.title);
    setActiveMenuId(null);
  };

  const handleSaveRename = (id: string, e: React.FormEvent) => {
    e.preventDefault();
    if (editTitle.trim()) {
      onRenameChat(id, editTitle.trim());
    }
    setEditingChatId(null);
  };

  const filteredChats = chats.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const displayUser: User = user || {
    name: "Architect",
    email: "user@nova.ai",
    plan: "Enterprise",
  };

  const navGroups = [
    {
      title: "CHAT",
      items: [
        { id: "chat" as WorkspaceView, label: "General Chat", icon: MessageSquare },
      ]
    },
    {
      title: "KNOWLEDGE",
      items: [
        { id: "documents" as WorkspaceView, label: "Documents & RAG", icon: FileText },
        { id: "collections" as WorkspaceView, label: "Collections", icon: FolderKanban },
      ]
    },
    {
      title: "AI WORKSPACES",
      items: [
        { id: "research" as WorkspaceView, label: "Research Mode", icon: SearchIcon },
        { id: "writing" as WorkspaceView, label: "Writing Mode", icon: Edit2 },
        { id: "code" as WorkspaceView, label: "Developer Sandbox", icon: Code2 },
        { id: "data" as WorkspaceView, label: "Data Analysis", icon: BarChart3 },
        { id: "agents" as WorkspaceView, label: "AI Agents", icon: Bot },
      ]
    },
    {
      title: "PRODUCTIVITY",
      items: [
        { id: "prompts" as WorkspaceView, label: "Prompt Library", icon: BookOpen },
        { id: "templates" as WorkspaceView, label: "Chat Templates", icon: FileCode2 },
        { id: "saved" as WorkspaceView, label: "Saved Responses", icon: Bookmark },
      ]
    },
    {
      title: "SYSTEM",
      items: [
        { id: "dashboard" as WorkspaceView, label: "Platform Overview", icon: LayoutDashboard },
        { id: "settings" as WorkspaceView, label: "Settings", icon: SettingsIcon },
      ]
    }
  ];

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 w-72 bg-surface border-r border-border flex flex-col transition-transform duration-300 md:translate-x-0 md:static select-none ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      {/* Sidebar Header / Logo */}
      <div className="h-16 flex items-center justify-between px-5 border-b border-border">
        <div
          onClick={() => onChangeView("dashboard")}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-surface rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-indigo-500 dark:text-indigo-400" />
            </div>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-black tracking-wider text-foreground">
              NOVA AI
            </span>
            <span className="text-[10px] text-indigo-600 dark:text-indigo-400 font-bold uppercase tracking-widest">
              Platform OS
            </span>
          </div>
        </div>

        {/* Mobile close button */}
        <button
          onClick={onClose}
          className="md:hidden p-1.5 rounded-lg hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Primary Action Button: New Chat */}
      <div className="p-4 pb-2">
        <button
          onClick={() => {
            onNewChat();
            onChangeView("chat");
            onClose();
          }}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-xl shadow-indigo-600/10 hover:shadow-indigo-600/25 transition-all duration-200 active:scale-[0.99] cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Navigation Workspace Menu Groups */}
      <div className="px-3 py-2 space-y-3 overflow-y-auto max-h-[45vh] border-b border-border scrollbar-thin">
        {navGroups.map((group) => (
          <div key={group.title} className="space-y-0.5">
            <div className="px-3 py-1 text-[9px] font-bold text-muted-foreground/80 tracking-wider uppercase">
              {group.title}
            </div>
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onChangeView(item.id);
                    onClose();
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                    isActive
                      ? "bg-indigo-600/10 text-indigo-600 dark:text-indigo-300 border-indigo-500/20"
                      : "text-muted-foreground hover:text-foreground hover:bg-surface-hover border-transparent"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-indigo-600 dark:text-indigo-400" : "text-muted-foreground"}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Search Input Box */}
      <div className="px-4 pt-3 pb-1">
        <div className="relative">
          <Search className="absolute left-3.5 top-2.5 w-3.5 h-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-surface border border-border rounded-xl py-2 pl-9 pr-8 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-indigo-500/50 transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-2 text-muted-foreground hover:text-foreground p-0.5 rounded cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Recents Scrollable List */}
      <div className="flex-grow overflow-y-auto px-2 py-1 space-y-1">
        <div className="px-3 py-1.5 text-[10px] font-bold text-muted-foreground tracking-wider uppercase flex items-center justify-between">
          <span>Recent History</span>
          <span className="text-muted-foreground font-mono text-[9px]">{filteredChats.length}</span>
        </div>

        {filteredChats.length === 0 ? (
          <div className="px-4 py-6 text-center text-xs text-muted-foreground italic">
            {searchQuery ? "No matching chats" : "No active history"}
          </div>
        ) : (
          <div className="space-y-0.5">
            {filteredChats.map((chat) => {
              const isActive = chat.id === activeChatId && activeView === "chat";
              const isEditing = chat.id === editingChatId;

              return (
                <div
                  key={chat.id}
                  onClick={() => {
                    if (!isEditing) {
                      onSelectChat(chat.id);
                      onChangeView("chat");
                      onClose();
                    }
                  }}
                  className={`group relative flex items-center justify-between px-3 py-2.5 rounded-xl border transition-all duration-150 cursor-pointer ${
                    isActive
                      ? "bg-indigo-600/10 text-indigo-600 dark:text-indigo-300 font-medium border-indigo-500/20"
                      : "text-muted-foreground hover:bg-surface-hover border-transparent hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0 flex-grow">
                    <MessageSquare className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? "text-indigo-600 dark:text-indigo-400" : "text-muted-foreground"}`} />
                    {isEditing ? (
                      <form
                        onSubmit={(e) => handleSaveRename(chat.id, e)}
                        className="flex items-center gap-1 w-full"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <input
                          type="text"
                          className="bg-surface text-foreground px-2 py-0.5 text-xs rounded border border-indigo-500 outline-none w-full"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          autoFocus
                          onBlur={(e) => handleSaveRename(chat.id, e as unknown as React.FormEvent)}
                          onKeyDown={(e) => {
                            if (e.key === "Escape") {
                              setEditingChatId(null);
                            }
                          }}
                        />
                        <button
                          type="submit"
                          className="p-0.5 bg-indigo-600 text-white rounded hover:bg-indigo-500 cursor-pointer"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      </form>
                    ) : (
                      <span className="text-xs truncate pr-2">{chat.title}</span>
                    )}
                  </div>

                  {!isEditing && (
                    <div className="relative chat-menu-container">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          const nextId = activeMenuId === chat.id ? null : chat.id;
                          setActiveMenuId(nextId);
                          setConfirmDeleteId(null);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-all cursor-pointer"
                        aria-label="Conversation options"
                        aria-expanded={activeMenuId === chat.id}
                      >
                        <MoreVertical className="w-3.5 h-3.5" />
                      </button>

                      {activeMenuId === chat.id && (
                        <div className="absolute right-0 mt-1 w-38 bg-surface-elevated border border-border rounded-xl shadow-2xl z-50 p-1 glass-panel">
                          <button
                            onClick={(e) => handleStartRename(chat, e)}
                            className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left text-xs text-foreground hover:bg-surface-hover cursor-pointer"
                          >
                            <Edit2 className="w-3.5 h-3.5 text-muted-foreground" />
                            Rename
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDuplicateChat(chat.id);
                              setActiveMenuId(null);
                            }}
                            className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left text-xs text-foreground hover:bg-surface-hover cursor-pointer"
                          >
                            <Copy className="w-3.5 h-3.5 text-muted-foreground" />
                            Duplicate
                          </button>
                          <div className="border-t border-border my-1" />
                          {confirmDeleteId === chat.id ? (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onDeleteChat(chat.id);
                                setConfirmDeleteId(null);
                                setActiveMenuId(null);
                              }}
                              className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left text-xs bg-danger text-white hover:bg-danger/90 font-semibold transition-all cursor-pointer"
                            >
                              <Check className="w-3.5 h-3.5 text-white" />
                              Confirm Delete
                            </button>
                          ) : (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setConfirmDeleteId(chat.id);
                              }}
                              className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left text-xs text-danger hover:bg-danger/10 cursor-pointer"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              Delete
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Sidebar Footer User Section */}
      <div className="p-3 border-t border-border relative" ref={userMenuRef}>
        <button
          onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
          className="w-full flex items-center justify-between p-2.5 rounded-2xl hover:bg-surface-hover transition-all cursor-pointer"
          aria-label="User profile menu"
          aria-expanded={isUserMenuOpen}
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 border border-border flex items-center justify-center font-bold text-xs text-white uppercase flex-shrink-0 shadow-md">
              {displayUser.name.charAt(0)}
            </div>
            <div className="text-left min-w-0">
              <p className="text-xs font-bold text-foreground truncate">{displayUser.name}</p>
              <p className="text-[10px] text-indigo-600 dark:text-indigo-400 font-medium truncate">{displayUser.plan}</p>
            </div>
          </div>
          <ChevronUp
            className={`w-4 h-4 text-muted-foreground transition-transform duration-200 ${
              isUserMenuOpen ? "transform rotate-180" : ""
            }`}
          />
        </button>

        {isUserMenuOpen && (
          <div className="absolute bottom-16 left-3 right-3 bg-surface-elevated border border-border rounded-2xl shadow-2xl p-1.5 z-50 glass-panel animate-in fade-in slide-in-from-bottom-2 duration-150">
            <button
              onClick={() => {
                setIsUserMenuOpen(false);
                onOpenSettings();
                onClose();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left text-xs text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
            >
              <SettingsIcon className="w-4 h-4 text-muted-foreground" />
              Account Settings
            </button>
            <button
              onClick={() => {
                setTheme(theme === "dark" ? "light" : "dark");
              }}
              className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-left text-xs text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                {theme === "dark" ? <Sun className="w-4 h-4 text-amber-500" /> : <Moon className="w-4 h-4 text-indigo-500" />}
                <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
              </div>
            </button>
            <button
              onClick={() => {
                setIsUserMenuOpen(false);
                onOpenCommandPalette();
                onClose();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left text-xs text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
            >
              <Keyboard className="w-4 h-4 text-muted-foreground" />
              Command Palette (Ctrl+K)
            </button>
            <div className="border-t border-border my-1" />
            <button
              onClick={() => {
                setIsUserMenuOpen(false);
                onSignOut();
                onClose();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left text-xs text-danger hover:bg-danger/10 transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
              Sign out
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
