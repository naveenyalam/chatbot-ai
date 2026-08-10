"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Settings,
  Moon,
  Sun,
  Tv,
  MessageSquare,
  Shield,
  Trash2,
  Cpu,
  FileText,
  User,
  Sliders,
  Database,
  Lock,
} from "lucide-react";
import { useApp } from "@/components/providers/ThemeProvider";
import { ConfirmationModal } from "@/components/ui/ConfirmationModal";

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onClearChats?: () => void;
}

type TabType = "appearance" | "model" | "chat" | "documents" | "account" | "security";

export function SettingsPanel({
  isOpen,
  onClose,
  onClearChats,
}: SettingsPanelProps) {
  const { theme, setTheme, settings, updateSetting } = useApp();
  const [activeTab, setActiveTab] = useState<TabType>("appearance");
  const [clearModalOpen, setClearModalOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const animate = settings.animationsEnabled;

  // Handle outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
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

  const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  } as const;

  const panelVariants = {
    hidden: { x: "100%" },
    visible: {
      x: 0,
      transition: { type: "spring", damping: 25, stiffness: 250 } as const,
    },
  } as const;

  const handleConfirmClear = () => {
    if (onClearChats) {
      onClearChats();
    }
    setClearModalOpen(false);
    onClose();
  };

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm"
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={animate ? overlayVariants : undefined}
            style={!animate ? { opacity: 1 } : {}}
          >
            <motion.div
              ref={panelRef}
              className="w-full max-w-lg h-full bg-surface-primary border-l border-border-subtle shadow-2xl flex flex-col glass-panel"
              variants={animate ? panelVariants : undefined}
              style={!animate ? { x: 0 } : {}}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-5 border-b border-border-subtle">
                <div className="flex items-center gap-2.5">
                  <Settings className="w-5 h-5 text-accent animate-spin-slow" />
                  <h2 className="text-lg font-semibold text-text-primary">System Configuration</h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-lg hover:bg-surface-secondary text-text-muted hover:text-text-primary transition-colors cursor-pointer"
                  aria-label="Close settings"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content Body */}
              <div className="flex-grow flex flex-col sm:flex-row overflow-hidden">
                {/* Tab Navigation */}
                <div className="w-full sm:w-2/5 border-b sm:border-b-0 sm:border-r border-border-subtle bg-surface-secondary/20 py-2 sm:py-4 flex flex-row sm:flex-col overflow-x-auto sm:overflow-x-visible gap-1 px-2.5 shrink-0 scrollbar-none">
                  {[
                    { id: "appearance", label: "Appearance", icon: Tv },
                    { id: "model", label: "AI Engine", icon: Cpu },
                    { id: "chat", label: "Chat Style", icon: MessageSquare },
                    { id: "documents", label: "Knowledge RAG", icon: FileText },
                    { id: "account", label: "User Account", icon: User },
                    { id: "security", label: "Data Security", icon: Shield },
                  ].map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as TabType)}
                        className={`flex items-center gap-3 px-3 py-2 sm:py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer shrink-0 ${
                          isActive
                            ? "bg-accent/15 text-accent border border-accent/20"
                            : "text-text-muted hover:text-text-primary hover:bg-surface-secondary"
                        }`}
                      >
                        <Icon className="w-4.5 h-4.5 flex-shrink-0" />
                        <span className="truncate">{tab.label}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Tab Content Panels */}
                <div className="w-full sm:w-3/5 p-5 sm:p-6 overflow-y-auto select-none flex-grow">
                  {/* 1. Appearance Section */}
                  {activeTab === "appearance" && (
                    <div className="space-y-6">
                      <div>
                        <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-3">
                          Theme Mode
                        </h3>
                        <div className="grid grid-cols-2 gap-2.5">
                          <button
                            onClick={() => setTheme("dark")}
                            className={`p-3 rounded-xl border flex flex-col items-center gap-2 text-xs font-medium cursor-pointer transition-all ${
                              theme === "dark"
                                ? "border-accent bg-accent/10 text-accent"
                                : "border-border-subtle text-text-muted hover:text-text-primary hover:bg-surface-secondary"
                            }`}
                          >
                            <Moon className="w-4 h-4" />
                            <span>Dark Mode</span>
                          </button>
                          <button
                            onClick={() => setTheme("light")}
                            className={`p-3 rounded-xl border flex flex-col items-center gap-2 text-xs font-medium cursor-pointer transition-all ${
                              theme === "light"
                                ? "border-accent bg-accent/10 text-accent"
                                : "border-border-subtle text-text-muted hover:text-text-primary hover:bg-surface-secondary"
                            }`}
                          >
                            <Sun className="w-4 h-4" />
                            <span>Light Mode</span>
                          </button>
                        </div>
                      </div>

                      <div className="space-y-4 pt-2">
                        <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-2">
                          Visual Preferences
                        </h3>
                        {/* Animations Toggle */}
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs font-semibold text-text-primary">Interface Animations</p>
                            <p className="text-[10px] text-text-muted leading-tight mt-0.5">Smooth UI transitions and glows</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              className="sr-only peer"
                              checked={settings.animationsEnabled}
                              onChange={(e) => updateSetting("animationsEnabled", e.target.checked)}
                            />
                            <div className="w-9 h-5 bg-border-subtle rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent"></div>
                          </label>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 2. AI Engine Section */}
                  {activeTab === "model" && (
                    <div className="space-y-6">
                      <div>
                        <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-3">
                          AI Core Profile
                        </h3>
                        <div className="p-3.5 rounded-xl border border-border-subtle bg-surface-secondary/35 text-xs text-text-muted leading-relaxed space-y-2">
                          <p className="font-bold text-text-primary flex items-center gap-1.5">
                            <Cpu className="w-3.5 h-3.5 text-accent" />
                            NOVA Intelligence 3.5
                          </p>
                          <p className="text-[11px]">
                            Currently loaded reasoning model engine optimized for semantic analysis, synthesis, code execution, and cognitive planning.
                          </p>
                        </div>
                      </div>

                      <div className="space-y-4 pt-1">
                        <div>
                          <label className="text-[10px] font-bold text-text-muted uppercase tracking-wider block mb-2">Context Window Length</label>
                          <input
                            type="range"
                            min="1"
                            max="3"
                            defaultValue="2"
                            className="w-full accent-accent bg-border-subtle h-1 rounded-lg outline-none cursor-pointer mt-1"
                          />
                          <div className="flex justify-between text-[9px] text-text-muted/80 font-semibold mt-1.5">
                            <span>Fast Stream</span>
                            <span>Balanced</span>
                            <span>Deep Context</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 3. Chat Style Section */}
                  {activeTab === "chat" && (
                    <div className="space-y-5">
                      <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-1">
                        Conversation Settings
                      </h3>
                      <div className="space-y-4">
                        {/* Send with Enter Toggle */}
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs font-semibold text-text-primary">Send with Enter</p>
                            <p className="text-[10px] text-text-muted leading-tight mt-0.5">Press Enter to dispatch messages</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              className="sr-only peer"
                              checked={settings.sendWithEnter}
                              onChange={(e) => updateSetting("sendWithEnter", e.target.checked)}
                            />
                            <div className="w-9 h-5 bg-border-subtle rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent"></div>
                          </label>
                        </div>

                        {/* Compact Mode Toggle */}
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs font-semibold text-text-primary">Compact Mode</p>
                            <p className="text-[10px] text-text-muted leading-tight mt-0.5">Reduce padding and messaging density</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              className="sr-only peer"
                              checked={settings.compactMode}
                              onChange={(e) => updateSetting("compactMode", e.target.checked)}
                            />
                            <div className="w-9 h-5 bg-border-subtle rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent"></div>
                          </label>
                        </div>

                        {/* Sound Effects Toggle */}
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs font-semibold text-text-primary">Audio Feedback</p>
                            <p className="text-[10px] text-text-muted leading-tight mt-0.5">Subtle sound effects on actions</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              className="sr-only peer"
                              checked={settings.soundEffectsEnabled}
                              onChange={(e) => updateSetting("soundEffectsEnabled", e.target.checked)}
                            />
                            <div className="w-9 h-5 bg-border-subtle rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent"></div>
                          </label>
                        </div>

                        {/* AI Response Style */}
                        <div className="space-y-1.5 pt-2 border-t border-border-subtle">
                          <label className="text-xs font-semibold text-text-primary block">AI Response Detail Style</label>
                          <select
                            value={settings.responseStyle || "balanced"}
                            onChange={(e) => updateSetting("responseStyle", e.target.value as any)}
                            className="w-full bg-surface-secondary border border-border-subtle rounded-xl px-3 py-2 text-xs text-text-primary outline-none focus:border-accent font-medium"
                          >
                            <option value="concise">Concise & Direct (Short bullet points)</option>
                            <option value="balanced">Balanced (Standard comprehensive response)</option>
                            <option value="detailed">In-Depth & Detailed (Deep explanations)</option>
                          </select>
                        </div>

                        {/* AI Response Tone */}
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-text-primary block">AI Response Tone</label>
                          <select
                            value={settings.responseTone || "professional"}
                            onChange={(e) => updateSetting("responseTone", e.target.value as any)}
                            className="w-full bg-surface-secondary border border-border-subtle rounded-xl px-3 py-2 text-xs text-text-primary outline-none focus:border-accent font-medium"
                          >
                            <option value="professional">Professional & Technical</option>
                            <option value="friendly">Friendly & Conversational</option>
                            <option value="technical">Strictly Academic / Code Heavy</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 4. Knowledge RAG Section */}
                  {activeTab === "documents" && (
                    <div className="space-y-6">
                      <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-1">
                        Retrieval Configuration
                      </h3>
                      <div className="space-y-4">
                        <div>
                          <label className="text-[10px] font-bold text-text-muted uppercase tracking-wider block mb-2">Semantic Chunk Limit</label>
                          <input
                            type="range"
                            min="2"
                            max="10"
                            value={settings.semanticChunkLimit}
                            onChange={(e) => updateSetting("semanticChunkLimit", parseInt(e.target.value, 10))}
                            className="w-full accent-accent bg-border-subtle h-1 rounded-lg outline-none cursor-pointer mt-1"
                          />
                          <div className="flex justify-between text-[9px] text-text-muted/80 font-semibold mt-1.5">
                            <span>2 chunks</span>
                            <span>{settings.semanticChunkLimit} chunks</span>
                            <span>10 chunks</span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-2">
                          <div>
                            <p className="text-xs font-semibold text-text-primary">Similarity Filtering</p>
                            <p className="text-[10px] text-text-muted leading-tight mt-0.5">Filter low score semantic results</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              className="sr-only peer"
                              checked={settings.similarityFiltering}
                              onChange={(e) => updateSetting("similarityFiltering", e.target.checked)}
                            />
                            <div className="w-9 h-5 bg-border-subtle rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent"></div>
                          </label>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 5. User Account Section */}
                  {activeTab === "account" && (
                    <div className="space-y-6">
                      <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-1">
                        Profile Details
                      </h3>
                      <div className="space-y-3.5 p-4 rounded-xl border border-border-subtle bg-surface-secondary/20 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-text-muted">Subscription Plan</span>
                          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider text-accent bg-accent/10 border border-accent/15">
                            Enterprise Tier
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-text-muted">Usage Budget</span>
                          <span className="font-mono text-emerald-400 font-semibold">Unlimited (Active)</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-text-muted">API Rate Limits</span>
                          <span className="text-text-primary font-semibold">60 requests / min</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 6. Data Security Section */}
                  {activeTab === "security" && (
                    <div className="space-y-6">
                      <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-1">
                        Data Control
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs font-semibold text-text-primary">Chat Retention</p>
                            <p className="text-[10px] text-text-muted leading-tight mt-0.5">Persist history on the cloud server</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              className="sr-only peer"
                              checked={settings.chatRetention}
                              onChange={(e) => updateSetting("chatRetention", e.target.checked)}
                            />
                            <div className="w-9 h-5 bg-border-subtle rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent"></div>
                          </label>
                        </div>

                        <div className="pt-4 border-t border-border-subtle/50">
                          <button
                            onClick={() => setClearModalOpen(true)}
                            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-red-500/20 bg-red-500/5 hover:bg-red-500/10 text-red-500 rounded-xl text-xs font-semibold tracking-wide transition-all cursor-pointer"
                          >
                            <Trash2 className="w-4 h-4" />
                            Clear All Conversations
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-border-subtle bg-surface-secondary/40 text-center text-[10px] text-text-muted">
                NOVA AI Enterprise Engine • Version 1.0.0
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <ConfirmationModal
        isOpen={clearModalOpen}
        title="Clear Conversations"
        message="Are you sure you want to permanently delete all conversations from your dashboard? This action is irreversible."
        confirmLabel="Clear All"
        cancelLabel="Cancel"
        onConfirm={handleConfirmClear}
        onClose={() => setClearModalOpen(false)}
      />
    </>
  );
}
