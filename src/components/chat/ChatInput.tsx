"use client";

import React, { useRef, useEffect, useState } from "react";
import {
  Paperclip,
  Cpu,
  Mic,
  ArrowUp,
  X,
  FileText,
  Image as ImageIcon,
  File,
  Loader2,
  Globe,
  BookOpen,
  Terminal,
  BarChart2,
  PenTool,
  Square,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Attachment, WorkspaceView } from "@/types";
import { uploadDocument, DocumentResponse } from "@/lib/api/documents";

import { useApp } from "@/components/providers/ThemeProvider";
import { useToast } from "@/components/ui/Toast";

export type ToolType = "search" | "research" | "document" | "image" | "task";

interface ChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  isLoading?: boolean;
  onStop?: () => void;
  attachments: Attachment[];
  onAddAttachments: React.Dispatch<React.SetStateAction<Attachment[]>>;
  onRemoveAttachment: (id: string) => void;
  selectedTool: ToolType | null;
  activeView?: WorkspaceView;
  placeholder?: string;
  onSelectTool: (tool: ToolType | null) => void;
  onAttachClick?: () => void;
  onUploadComplete?: (doc: DocumentResponse) => void;
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  isLoading = false,
  onStop,
  attachments,
  onAddAttachments,
  onRemoveAttachment,
  selectedTool,
  activeView = "chat",
  placeholder,
  onSelectTool,
  onAttachClick,
  onUploadComplete,
}: ChatInputProps) {
  const { settings } = useApp();
  const toast = useToast();
  const [isFocused, setIsFocused] = useState(false);
  const [isToolsOpen, setIsToolsOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toolsRef = useRef<HTMLDivElement>(null);
  
  const charLimit = 4000;

  // Auto-grow textarea height
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, [value]);

  // Click outside Tools Popover
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (toolsRef.current && !toolsRef.current.contains(e.target as Node)) {
        setIsToolsOpen(false);
      }
    };
    if (isToolsOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isToolsOpen]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      if (settings.sendWithEnter) {
        e.preventDefault();
        if ((value.trim() || attachments.length > 0) && !isLoading) {
          onSubmit();
        }
      }
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    if (val.length <= charLimit) {
      onChange(val);
    }
  };

  // Handle Attachment Upload Simulation
  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  const uploadFiles = (files: File[]) => {
    files.forEach(async (file) => {
      const id = Math.random().toString(36).substring(7);
      const newAttachment: Attachment = {
        id,
        name: file.name,
        size: file.size,
        type: file.type,
        status: "uploading",
        progress: 0,
      };

      onAddAttachments((prev) => [...prev, newAttachment]);

      try {
        const doc = await uploadDocument(file, (percent) => {
          onAddAttachments((prev) =>
            prev.map((a) => (a.id === id ? { ...a, progress: percent } : a))
          );
        });

        onAddAttachments((prev) =>
          prev.map((a) =>
            a.id === id
              ? { ...a, id: doc.id, progress: 100, status: "ready" }
              : a
          )
        );

        if (onUploadComplete) {
          onUploadComplete(doc);
        }
      } catch (err: any) {
        console.error("Live upload failed:", err);
        onAddAttachments((prev) =>
          prev.map((a) => (a.id === id ? { ...a, progress: 0, status: "error" } : a))
        );
      }
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const selectedFiles = Array.from(e.target.files);
    uploadFiles(selectedFiles);
    e.target.value = "";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadFiles(Array.from(e.dataTransfer.files));
    }
  };

  // Real Web Speech API Recognition
  const toggleVoice = () => {
    if (isListening) {
      setIsListening(false);
      return;
    }

    const SpeechRecognition =
      (window as unknown as { SpeechRecognition?: any; webkitSpeechRecognition?: any }).SpeechRecognition ||
      (window as unknown as { SpeechRecognition?: any; webkitSpeechRecognition?: any }).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      toast.warning("Voice speech recognition is not supported in your browser.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0].transcript)
          .join("");
        onChange(transcript);
      };

      recognition.onerror = (err: any) => {
        console.error("Speech recognition error:", err);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
    } catch (err) {
      console.error("Failed to start speech recognition:", err);
      setIsListening(false);
    }
  };

  const getAttachmentIcon = (type: string) => {
    if (type.startsWith("image/")) return <ImageIcon className="w-3.5 h-3.5 text-indigo-400" />;
    if (type.includes("pdf") || type.includes("doc") || type.includes("text")) {
      return <FileText className="w-3.5 h-3.5 text-blue-400" />;
    }
    return <File className="w-3.5 h-3.5 text-text-muted" />;
  };

  const tools = [
    { id: "search", name: "Web Search", desc: "Scan details live from the web", icon: Globe },
    { id: "research", name: "Deep Research", desc: "Execute multi-step synthesis", icon: BookOpen },
    { id: "document", name: "Document Search", desc: "Search uploaded files/RAG database", icon: FileText },
    { id: "image", name: "Image Analysis", desc: "Analyze visual elements and charts", icon: ImageIcon },
    { id: "task", name: "Autonomous Agent", desc: "Executes code, math & advanced tools autonomously", icon: Terminal },
  ] as const;

  const ActiveToolIcon = selectedTool ? tools.find(t => t.id === selectedTool)?.icon : null;

  const getPlaceholder = () => {
    if (placeholder) return placeholder;
    if (isListening) return "Listening...";
    switch (activeView) {
      case "research":
        return "Ask a research question or topic to analyze...";
      case "writing":
        return "Describe what you want to write, rewrite, or polish...";
      case "code":
        return "Describe a coding problem, debugging task, or algorithm...";
      case "documents":
        return "Ask questions about your indexed documents...";
      case "data":
        return "Ask about your dataset, statistical metrics, or trends...";
      case "agents":
        return "Describe a complex multi-step task for the AI Agent...";
      default:
        return "Ask Nova anything... (Shift+Enter for new line)";
    }
  };

  return (
    <div className="w-full px-4 md:px-6 pb-6 pt-2 bg-gradient-to-t from-background via-background/95 to-transparent sticky bottom-0 z-30">
      <div className="max-w-3xl mx-auto relative">
        
        {/* Hidden File Input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          multiple
        />

        {/* Tools Popover Menu */}
        {isToolsOpen && (
          <div
            ref={toolsRef}
            className="absolute bottom-full left-4 mb-3 w-72 bg-surface-primary border border-border-subtle rounded-2xl shadow-2xl glass-panel p-2 z-40 animate-in fade-in slide-in-from-bottom-2 duration-200 select-none"
          >
            <div className="px-3 py-1.5 text-[10px] font-bold text-text-muted tracking-wider uppercase border-b border-border-subtle/55 mb-1.5">
              Select Workspace Agent
            </div>
            <div className="space-y-0.5">
              {tools.map((tool) => {
                const Icon = tool.icon;
                const isSelected = selectedTool === tool.id;
                return (
                  <button
                    key={tool.id}
                    onClick={() => {
                      const willSelect = isSelected ? null : tool.id;
                      onSelectTool(willSelect);
                      setIsToolsOpen(false);
                      if (willSelect === "document") {
                        onAttachClick?.();
                      } else if (willSelect === "image") {
                        fileInputRef.current?.click();
                      }
                    }}
                    className={cn(
                      "w-full flex items-start gap-3 p-2 rounded-xl text-left transition-all",
                      isSelected
                        ? "bg-accent/15 border border-accent/25 text-text-primary"
                        : "border border-transparent hover:bg-surface-secondary text-text-muted hover:text-text-primary"
                    )}
                  >
                    <div className={cn(
                      "p-1.5 rounded-lg border border-border-subtle bg-surface-secondary/70 mt-0.5",
                      isSelected && "border-accent/40 text-accent"
                    )}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-grow">
                      <p className="text-xs font-semibold">{tool.name}</p>
                      <p className="text-[10px] text-text-muted/80 leading-normal mt-0.5">{tool.desc}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Input container */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "glass-panel rounded-2xl border transition-all duration-300 flex flex-col p-2 bg-surface-primary/75 relative",
            isFocused
              ? "border-accent ring-1 ring-accent/30 shadow-[0_0_20px_rgba(99,102,241,0.06)] dark:shadow-[0_0_25px_rgba(129,140,248,0.06)]"
              : "border-border-subtle hover:border-border-subtle/80",
            isDragging && "border-accent bg-accent/5 ring-2 ring-accent/30"
          )}
        >
          {isDragging && (
            <div className="absolute inset-0 bg-accent/5 backdrop-blur-[1px] flex items-center justify-center rounded-2xl border-2 border-dashed border-accent z-40 pointer-events-none select-none">
              <span className="text-xs font-bold text-accent animate-pulse uppercase tracking-wider">Drop files to upload</span>
            </div>
          )}
          {/* Active File Attachments Shelf */}
          {attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 px-3 pt-2 pb-1.5 border-b border-border-subtle/40 select-none">
              {attachments.map((file) => (
                <div
                  key={file.id}
                  className={cn(
                    "flex items-center gap-2 pl-2.5 pr-1.5 py-1 rounded-xl text-xs border bg-surface-secondary/50",
                    file.status === "error" ? "border-rose-500/30 text-rose-300" : "border-border-subtle text-text-primary"
                  )}
                >
                  {file.status === "uploading" ? (
                    <Loader2 className="w-3.5 h-3.5 text-accent animate-spin" />
                  ) : (
                    getAttachmentIcon(file.type)
                  )}
                  <span className="max-w-[120px] truncate text-[11px] font-medium">{file.name}</span>
                  {file.status === "uploading" && (
                    <span className="text-[9px] text-text-muted font-mono">{file.progress}%</span>
                  )}
                  <button
                    onClick={() => onRemoveAttachment(file.id)}
                    className="p-0.5 rounded-md hover:bg-surface-secondary text-text-muted hover:text-text-primary transition-all ml-1 cursor-pointer"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Active Agent Badge inside textarea top line */}
          {selectedTool && (
            <div className="flex px-3 pt-2 select-none">
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider text-accent bg-accent/10 border border-accent/15">
                {ActiveToolIcon && <ActiveToolIcon className="w-3 h-3" />}
                {tools.find(t => t.id === selectedTool)?.name}
                <button
                  onClick={() => onSelectTool(null)}
                  className="hover:text-white transition-colors cursor-pointer"
                >
                  <X className="w-2.5 h-2.5 ml-1" />
                </button>
              </span>
            </div>
          )}

          {/* Text input area */}
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            disabled={isListening}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={getPlaceholder()}
            aria-label="Ask Nova anything"
            className="w-full bg-transparent resize-none outline-none border-none text-text-primary placeholder:text-text-muted px-3 pt-2.5 pb-1 text-xs md:text-sm leading-relaxed max-h-48 overflow-y-auto"
            style={{ minHeight: "24px" }}
          />

          {/* Action bar (buttons + indicators) */}
          <div className="flex items-center justify-between border-t border-border-subtle/50 mt-2.5 pt-2 px-1 select-none">
            {/* Left buttons (Attach, Tools, Voice) */}
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={onAttachClick || triggerFileSelect}
                disabled={isLoading}
                className={cn(
                  "p-2 rounded-xl text-text-muted hover:text-text-primary hover:bg-surface-secondary/60 transition-colors cursor-pointer",
                  isLoading && "opacity-40 cursor-not-allowed"
                )}
                aria-label="Attach file"
              >
                <Paperclip className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setIsToolsOpen(!isToolsOpen)}
                disabled={isLoading}
                className={cn(
                  "p-2 rounded-xl text-text-muted hover:text-text-primary hover:bg-surface-secondary/60 transition-colors cursor-pointer",
                  isLoading && "opacity-40 cursor-not-allowed",
                  isToolsOpen && "bg-surface-secondary/80 text-accent border border-border-subtle/40"
                )}
                aria-label="Add tools"
              >
                <Cpu className="w-4 h-4" />
              </button>

              {/* Voice button with ring animation */}
              <div className="relative">
                <button
                  type="button"
                  onClick={toggleVoice}
                  disabled={isLoading}
                  className={cn(
                    "p-2 rounded-xl text-text-muted hover:text-text-primary hover:bg-surface-secondary/60 transition-all cursor-pointer relative z-10",
                    isLoading && "opacity-40 cursor-not-allowed",
                    isListening && "text-accent bg-accent/5"
                  )}
                  aria-label="Voice command"
                >
                  <Mic className="w-4 h-4" />
                </button>
                {isListening && (
                  <div className="absolute inset-0 bg-accent/20 rounded-xl animate-ping opacity-60 scale-125 z-0" />
                )}
              </div>
              
              {isListening && (
                <span className="text-[10px] text-accent font-bold uppercase tracking-wider animate-pulse ml-1">
                  Listening...
                </span>
              )}
            </div>

            {/* Right details (Token counts + Send / Stop button) */}
            <div className="flex items-center gap-3">
              {value.length > 50 && (
                <span className="text-[9px] md:text-[10px] text-text-muted/80 font-mono">
                  {value.length} / {charLimit}
                </span>
              )}

              {isLoading ? (
                // Stop Generation button
                <button
                  type="button"
                  onClick={onStop}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/25 border border-rose-500/25 text-rose-300 transition-all hover:scale-[1.01] cursor-pointer text-xs font-semibold"
                  aria-label="Stop generating"
                >
                  <Square className="w-3.5 h-3.5 fill-rose-300" />
                  <span>Stop</span>
                </button>
              ) : (
                // Send button
                <button
                  type="button"
                  disabled={(!value.trim() && attachments.length === 0) || isLoading}
                  onClick={onSubmit}
                  className={cn(
                    "p-2 rounded-xl transition-all flex items-center justify-center cursor-pointer",
                    (value.trim() || attachments.length > 0) && !isLoading
                      ? "bg-accent text-white hover:bg-accent-hover hover:-translate-y-[1px] active:translate-y-0 shadow-lg shadow-accent/15"
                      : "bg-surface-secondary text-text-muted/40 cursor-not-allowed border border-border-subtle"
                  )}
                  aria-label="Send message"
                >
                  <ArrowUp className="w-4.5 h-4.5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
