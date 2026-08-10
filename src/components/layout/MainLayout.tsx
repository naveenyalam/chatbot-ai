"use client";

import React, { useEffect, useState } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { SettingsPanel } from "../settings/SettingsPanel";
import { CommandPalette } from "../ui/CommandPalette";
import { Chat, User, WorkspaceView } from "@/types";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

interface MainLayoutProps {
  children: React.ReactNode;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  settingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;
  commandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;
  chats: Chat[];
  activeChatId: string | null;
  activeView: WorkspaceView;
  onChangeView: (view: WorkspaceView) => void;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string) => void;
  onRenameChat: (id: string, newTitle: string) => void;
  onDuplicateChat: (id: string) => void;
  onClearChats: () => void;
  selectedModel: string;
  onSelectModel: (model: string) => void;
  user: User | null;
  onSignOut: () => void;
  onExportChat?: (format: "md" | "json" | "txt") => void;
}

export function MainLayout({
  children,
  sidebarOpen,
  setSidebarOpen,
  settingsOpen,
  setSettingsOpen,
  commandPaletteOpen,
  setCommandPaletteOpen,
  chats,
  activeChatId,
  activeView,
  onChangeView,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat,
  onDuplicateChat,
  onClearChats,
  selectedModel,
  onSelectModel,
  user,
  onSignOut,
  onExportChat,
}: MainLayoutProps) {
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  // Command palette (Ctrl+K), New Chat (Ctrl+N) & Escape hotkeys
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen(true);
      } else if ((e.ctrlKey || e.metaKey) && e.key === "n") {
        e.preventDefault();
        onNewChat();
        onChangeView("chat");
      } else if (e.key === "Escape") {
        setShortcutsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setCommandPaletteOpen, onNewChat, onChangeView]);

  const activeChat = chats.find((c) => c.id === activeChatId) || null;

  const handleCommandPaletteAction = (action: string) => {
    setCommandPaletteOpen(false);
    if (action === "new-chat") {
      onNewChat();
      onChangeView("chat");
    } else if (action === "chat") {
      onChangeView("chat");
    } else if (action === "settings") {
      setSettingsOpen(true);
    } else if (action === "documents") {
      onChangeView("documents");
    } else if (action === "agents") {
      onChangeView("agents");
    } else if (action === "code") {
      onChangeView("code");
    } else if (action === "shortcuts") {
      setShortcutsOpen(true);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground relative selection:bg-indigo-500/30">
      {/* Mobile sidebar drawer overlay */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/60 z-35 md:hidden backdrop-blur-md transition-opacity"
        />
      )}

      {/* Sidebar Panel */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        chats={chats}
        activeChatId={activeChatId}
        activeView={activeView}
        onChangeView={onChangeView}
        onSelectChat={onSelectChat}
        onNewChat={onNewChat}
        onDeleteChat={onDeleteChat}
        onRenameChat={onRenameChat}
        onDuplicateChat={onDuplicateChat}
        onOpenSettings={() => setSettingsOpen(true)}
        onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        user={user}
        onSignOut={onSignOut}
      />

      {/* Main Workspace Frame */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative">
        {/* Floating Header */}
        <Header
          onOpenSidebar={() => setSidebarOpen(true)}
          onOpenSettings={() => setSettingsOpen(true)}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
          chatTitle={activeChat ? activeChat.title : null}
          selectedModel={selectedModel}
          onSelectModel={onSelectModel}
          activeView={activeView}
          onChangeView={onChangeView}
          onExportChat={onExportChat}
        />

        {/* Workspace Content */}
        <main className="flex-1 flex flex-col min-h-0 bg-background relative overflow-hidden">
          {children}
        </main>
      </div>

      {/* Settings Overlay Slide-over */}
      <SettingsPanel
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onClearChats={onClearChats}
      />

      {/* Command Palette Overlay */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onSelectAction={handleCommandPaletteAction}
        chats={chats}
        onSelectChat={onSelectChat}
      />

      {/* Keyboard Shortcuts Dialog */}
      <AnimatePresence>
        {shortcutsOpen && (
          <div className="fixed inset-0 z-55 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md bg-surface-elevated border border-border rounded-3xl p-6 shadow-2xl relative glass-panel text-foreground"
            >
              <div className="flex items-center justify-between mb-4 border-b border-border pb-3">
                <h3 className="text-sm font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
                  Keyboard Shortcuts
                </h3>
                <button
                  onClick={() => setShortcutsOpen(false)}
                  className="p-1 rounded-lg hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between py-2 border-b border-border/40">
                  <span className="text-xs text-muted-foreground">Open Command Palette</span>
                  <kbd className="px-2 py-1 bg-surface border border-border rounded text-[10px] font-mono text-foreground">Ctrl + K</kbd>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-border/40">
                  <span className="text-xs text-muted-foreground">New Conversation</span>
                  <kbd className="px-2 py-1 bg-surface border border-border rounded text-[10px] font-mono text-foreground">Ctrl + N</kbd>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-xs text-muted-foreground">Close Modals / Overlays</span>
                  <kbd className="px-2 py-1 bg-surface border border-border rounded text-[10px] font-mono text-foreground">Esc</kbd>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShortcutsOpen(false)}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20 active:scale-[0.98] transition-all cursor-pointer"
                >
                  Dismiss
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
