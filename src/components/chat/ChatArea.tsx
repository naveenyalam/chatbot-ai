"use client";

import React, { useRef, useEffect, useState } from "react";
import {
  Copy,
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  Check,
  Sparkles,
  User,
  Edit2,
  ArrowDown,
  MoreHorizontal,
  ChevronDown,
  ChevronUp,
  Clock,
  Eye,
  Trash2,
} from "lucide-react";
import { Layers, FileText, Database, Info, X as XIcon, ChevronRight } from "lucide-react";
import { Chat, Message, Attachment, WorkspaceView } from "@/types";
import { ChatWelcome } from "./ChatWelcome";
import { ChatInput, ToolType } from "./ChatInput";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { ToolActivity } from "./ToolActivity";
import { CodeExecutionResult } from "./CodeExecutionResult";
import { ImageMessage } from "./ImageMessage";
import { ImageViewerModal } from "./ImageViewerModal";
import { downloadImage } from "@/lib/api/client";
import { useApp } from "@/components/providers/ThemeProvider";
import { useToast } from "@/components/ui/Toast";
import { cn } from "@/lib/utils";

import { DocumentResponse } from "@/lib/api/documents";

interface ChatAreaProps {
  activeChat: Chat | null;
  onSendMessage: (content: string) => void;
  onEditMessage: (messageId: string, newContent: string) => void;
  onRegenerateMessage: (messageId: string) => void;
  onStopGeneration: () => void;
  onDeleteMessage?: (messageId: string) => void;
  isLoading: boolean;
  activeView?: WorkspaceView;
  selectedModel?: string;
  selectedDocIds?: string[];
  documents?: DocumentResponse[];
  
  // Attachments state
  attachments: Attachment[];
  onAddAttachments: React.Dispatch<React.SetStateAction<Attachment[]>>;
  onRemoveAttachment: (id: string) => void;

  // Selected tool state
  selectedTool: ToolType | null;
  onSelectTool: (tool: ToolType | null) => void;

  // Document RAG attachment & citations callbacks
  onAttachClick?: () => void;
  onOpenCitations?: (sources: any[], highlightIndex: number) => void;
  onUploadComplete?: (doc: DocumentResponse) => void;
}

export function ChatArea({
  activeChat,
  onSendMessage,
  onEditMessage,
  onRegenerateMessage,
  onStopGeneration,
  onDeleteMessage,
  isLoading,
  activeView = "chat",
  selectedModel = "intelligence",
  selectedDocIds = [],
  documents = [],
  attachments,
  onAddAttachments,
  onRemoveAttachment,
  selectedTool,
  onSelectTool,
  onAttachClick,
  onOpenCitations,
  onUploadComplete,
}: ChatAreaProps) {
  const { settings } = useApp();
  const toast = useToast();
  const [inputVal, setInputVal] = useState("");
  const draftsRef = useRef<Record<string, string>>({});
  const isSubmittingRef = useRef(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [ratings, setRatings] = useState<Record<string, "up" | "down" | null>>({});
  const [showContextDetails, setShowContextDetails] = useState(false);
  
  // User edit state
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editVal, setEditVal] = useState("");

  // Action popover state
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);

  // AI Image viewer modal state
  const [activeModalImage, setActiveModalImage] = useState<{ url: string; prompt?: string } | null>(null);

  // Scroll locks
  const [showScrollBottomBtn, setShowScrollBottomBtn] = useState(false);
  const [expandedThinking, setExpandedThinking] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const messages = activeChat?.messages || [];
  const animate = settings.animationsEnabled;

  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  useEffect(() => {
    const chatId = activeChat ? activeChat.id : "new-chat";
    setInputVal(draftsRef.current[chatId] || "");
  }, [activeChat]);

  const handleInputChange = (val: string) => {
    setInputVal(val);
    const chatId = activeChat ? activeChat.id : "new-chat";
    draftsRef.current[chatId] = val;
  };

  // Scroll on message change
  useEffect(() => {
    if (!showScrollBottomBtn) {
      scrollToBottom(animate ? "smooth" : "auto");
    }
  }, [messages.length, isLoading, animate, showScrollBottomBtn]);

  // Scroll on token stream chunk
  const lastMessage = messages[messages.length - 1];
  const lastMessageContent = lastMessage?.content;
  useEffect(() => {
    if (lastMessage?.isStreaming && !showScrollBottomBtn) {
      scrollToBottom("auto");
    }
  }, [lastMessageContent, lastMessage?.isStreaming, showScrollBottomBtn]);

  // Handle scroll trigger to show snap button
  const handleScroll = () => {
    const container = scrollContainerRef.current;
    if (!container) return;
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 120;
    setShowScrollBottomBtn(!isNearBottom);
  };

  const handleSend = () => {
    if ((!inputVal.trim() && attachments.length === 0) || isLoading || isSubmittingRef.current) return;
    isSubmittingRef.current = true;
    const chatId = activeChat ? activeChat.id : "new-chat";
    draftsRef.current[chatId] = "";
    onSendMessage(inputVal.trim());
    setInputVal("");
    setTimeout(() => {
      isSubmittingRef.current = false;
    }, 600);
  };

  const handleCopy = async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      toast.success("Response copied to clipboard");
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      toast.error("Failed to copy response");
      console.error("Failed to copy message", err);
    }
  };

  const handleRate = (id: string, rate: "up" | "down") => {
    setRatings((prev) => ({
      ...prev,
      [id]: prev[id] === rate ? null : rate,
    }));
  };

  const startEditing = (msg: Message) => {
    setEditingMessageId(msg.id);
    setEditVal(msg.content);
  };

  const saveEdit = (msgId: string) => {
    if (editVal.trim()) {
      onEditMessage(msgId, editVal.trim());
    }
    setEditingMessageId(null);
  };

  // Extract <thinking> blocks for clean folding
  const extractThinkingProcess = (content: string) => {
    const match = content.match(/<thinking>([\s\S]*?)<\/thinking>/);
    if (match) {
      const thinkingText = match[1].trim();
      const actualContent = content.replace(/<thinking>([\s\S]*?)<\/thinking>/, "").trim();
      return { thinkingText, actualContent };
    }
    return { thinkingText: null, actualContent: content };
  };

  const formatMessageTime = (isoString?: string) => {
    if (!isoString) return "";
    try {
      const date = new Date(isoString);
      if (isNaN(date.getTime())) {
        return "";
      }
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  const selectedDocs = documents.filter((d) => selectedDocIds.includes(d.id));

  return (
    <div className="flex-1 flex flex-col min-h-0 relative overflow-hidden">
      {/* Context Indicator Bar (STEP 5) */}
      <div className="border-b border-border/40 bg-surface/50 backdrop-blur-md px-4 py-1.5 flex items-center justify-between text-[11px] text-muted-foreground select-none">
        <div className="flex items-center gap-3 overflow-x-auto no-scrollbar">
          <span className="flex items-center gap-1 font-semibold text-foreground">
            <Layers className="w-3 h-3 text-indigo-400" />
            <span className="capitalize">{activeView} Workspace</span>
          </span>
          <span className="text-border-subtle">•</span>
          <span className="font-mono text-[10px] bg-surface-secondary px-2 py-0.5 rounded-full border border-border-subtle">
            {selectedModel === "fast" ? "NOVA Fast Latency" : selectedModel === "reason" ? "NOVA Reason DeepThink" : "NOVA Intelligence 3.5"}
          </span>
          <span className="text-border-subtle">•</span>
          <span>{messages.length} messages</span>
          {selectedDocIds.length > 0 && (
            <>
              <span className="text-border-subtle">•</span>
              <button
                onClick={() => setShowContextDetails(!showContextDetails)}
                className="flex items-center gap-1 font-medium text-indigo-400 hover:text-indigo-300 transition-colors cursor-pointer"
              >
                <FileText className="w-3 h-3" />
                <span>{selectedDocIds.length} docs indexed</span>
              </button>
            </>
          )}
        </div>

        {selectedDocIds.length > 0 && (
          <button
            onClick={() => setShowContextDetails(!showContextDetails)}
            className="p-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            <Info className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Expanded Context Details Drawer */}
      {showContextDetails && selectedDocs.length > 0 && (
        <div className="bg-surface-elevated border-b border-border p-3 text-xs animate-in slide-in-from-top-1 duration-150">
          <div className="flex items-center justify-between font-bold text-foreground mb-2">
            <span className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              Active Knowledge Base Documents ({selectedDocs.length})
            </span>
            <button onClick={() => setShowContextDetails(false)} className="text-muted-foreground hover:text-foreground">
              <XIcon className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {selectedDocs.map((doc) => (
              <div key={doc.id} className="p-2 rounded-xl bg-surface border border-border flex items-center justify-between truncate">
                <span className="truncate text-foreground text-[11px] font-medium">{doc.original_filename}</span>
                <span className="text-[9px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">RAG Ready</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {messages.length === 0 ? (
        <ChatWelcome onSelectPrompt={(prompt) => setInputVal(prompt)} activeView={activeView} />
      ) : (
        /* Messages History View */
        <div
          ref={scrollContainerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto px-4 py-6 md:px-6 space-y-6 scrollbar-thin select-text"
        >
          <div className="max-w-3xl mx-auto space-y-7 pb-4">
            {messages.map((msg) => {
              const isAssistant = msg.role === "assistant";
              const isRatedUp = ratings[msg.id] === "up";
              const isRatedDown = ratings[msg.id] === "down";
              const isEditing = editingMessageId === msg.id;

              // Parse reasoning thought processes
              const { thinkingText, actualContent } = isAssistant
                ? extractThinkingProcess(msg.content)
                : { thinkingText: null, actualContent: msg.content };

              const isThinkingFolded = expandedThinking[msg.id] !== false;

              return (
                <div
                  key={msg.id}
                  className={cn(
                    "flex gap-4 group/msg relative",
                    isAssistant ? "items-start" : "flex-row-reverse items-start"
                  )}
                >
                  {/* Avatar Icon */}
                  <div
                    className={cn(
                      "w-8.5 h-8.5 rounded-xl border flex-shrink-0 flex items-center justify-center font-bold text-xs select-none shadow-sm",
                      isAssistant
                        ? "bg-gradient-to-tr from-accent to-indigo-500 border-accent/20 text-white"
                        : "bg-surface-secondary border-border-subtle text-text-muted"
                    )}
                  >
                    {isAssistant ? (
                      <Sparkles className="w-4 h-4 text-white" />
                    ) : (
                      <User className="w-4 h-4 text-text-muted" />
                    )}
                  </div>

                  {/* Message Core Body */}
                  <div className={cn("flex flex-col max-w-[85%]", isAssistant ? "items-start" : "items-end")}>
                    {/* Header line metadata */}
                    <div className="flex items-center gap-2 mb-1.5 px-1 select-none">
                      <span className="text-[10px] font-bold text-text-muted tracking-widest uppercase">
                        {isAssistant ? "Nova" : "You"}
                      </span>
                      <span className="text-[9px] text-text-muted/60 flex items-center gap-1 font-mono">
                        <Clock className="w-2.5 h-2.5" />
                        {formatMessageTime(msg.timestamp)}
                      </span>
                    </div>

                    {/* Edit mode vs standard bubble */}
                    {!isAssistant && isEditing ? (
                      <div className="w-full min-w-[280px] sm:min-w-[450px] p-2.5 rounded-2xl border border-accent/40 bg-surface-secondary flex flex-col gap-2">
                        <textarea
                          value={editVal}
                          onChange={(e) => setEditVal(e.target.value)}
                          className="w-full min-h-[80px] bg-transparent outline-none border-none text-text-primary text-xs md:text-sm resize-none"
                        />
                        <div className="flex justify-end gap-2 text-xs">
                          <button
                            onClick={() => setEditingMessageId(null)}
                            className="px-3 py-1.5 rounded-lg hover:bg-surface-primary text-text-muted cursor-pointer font-medium"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={() => saveEdit(msg.id)}
                            className="px-3 py-1.5 rounded-lg bg-accent text-white hover:bg-accent-hover shadow-md cursor-pointer font-medium"
                          >
                            Save & Submit
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="relative">
                        {/* Text Container bubble */}
                        <div
                          className={cn(
                            "rounded-2xl text-xs md:text-sm leading-relaxed max-w-full break-words transition-all duration-200",
                            isAssistant
                              ? "bg-transparent border-none text-text-primary text-justify"
                              : "px-4 py-3 bg-surface-secondary/40 hover:bg-surface-secondary/55 border border-border-subtle hover:border-border-subtle/85 text-text-primary shadow-sm"
                          )}
                        >
                          {/* Rendering reasoning steps if present */}
                          {isAssistant && thinkingText && (
                            <div className="mb-4 w-full rounded-xl border border-border-subtle/60 bg-surface-secondary/20 overflow-hidden text-xs md:text-sm">
                              <button
                                onClick={() =>
                                  setExpandedThinking((prev) => ({
                                    ...prev,
                                    [msg.id]: !isThinkingFolded,
                                  }))
                                }
                                className="w-full flex items-center justify-between px-3.5 py-2.5 bg-surface-secondary/60 hover:bg-surface-secondary text-[10px] font-bold text-text-muted tracking-wider uppercase border-b border-border-subtle/30"
                              >
                                <span className="flex items-center gap-1.5">
                                  <Sparkles className="w-3 h-3 text-accent" />
                                  Reasoning thoughts
                                </span>
                                {isThinkingFolded ? (
                                  <ChevronUp className="w-3 h-3" />
                                ) : (
                                  <ChevronDown className="w-3 h-3" />
                                )}
                              </button>
                              {isThinkingFolded && (
                                <div className="p-3.5 space-y-1.5 text-text-muted font-mono leading-relaxed bg-surface-primary/10 select-none">
                                  {thinkingText.split("\n").map((step, sIdx) => (
                                    <div key={sIdx} className="flex gap-2">
                                      <span className="text-accent">•</span>
                                      <p>{step.replace(/^- /, "")}</p>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}

                          {/* Main Text Content */}
                          {(msg.statusMessage || msg.researchPlan) && msg.isStreaming && (
                            <div className="mb-4 p-4 rounded-xl border border-border-subtle bg-surface-secondary/40 space-y-3 glass-panel max-w-lg select-none">
                              <div className="flex items-center gap-3">
                                <div className="w-5 h-5 rounded-lg border border-accent/20 bg-accent/10 flex items-center justify-center flex-shrink-0">
                                  <Sparkles className="w-3.5 h-3.5 text-accent animate-pulse" />
                                </div>
                                <div className="flex-grow">
                                  <span className="text-[10px] font-bold text-accent uppercase tracking-wider">
                                    Agent Pipeline Status
                                  </span>
                                  <p className="text-xs font-semibold text-text-primary capitalize mt-0.5">
                                    {msg.statusMessage}...
                                  </p>
                                </div>
                              </div>
                              
                              {/* Display research query details if present */}
                              {msg.statusQuery && (
                                <p className="text-[10px] text-text-muted italic border-l-2 border-accent/40 pl-2">
                                  Querying: &quot;{msg.statusQuery}&quot;
                                </p>
                              )}

                              {/* Progress bar logic for deep research */}
                              {msg.statusMessage && (
                                <div className="w-full bg-surface-secondary/80 rounded-full h-1.5 overflow-hidden">
                                  <div
                                    className="bg-accent h-1.5 rounded-full transition-all duration-500"
                                    style={{
                                      width: 
                                        msg.statusMessage === "planning" ? "20%" :
                                        msg.statusMessage === "searching" ? (
                                          msg.statusQuery?.includes("Step 2") ? "40%" :
                                          msg.statusQuery?.includes("Step 3") ? "60%" :
                                          msg.statusQuery?.includes("Step 4") ? "80%" : "50%"
                                        ) :
                                        msg.statusMessage === "synthesizing" ? "95%" :
                                        msg.statusMessage === "analyzing" ? "75%" : "100%"
                                    }}
                                  />
                                </div>
                              )}

                              {/* Research subtopics checklist */}
                              {msg.researchPlan && msg.researchPlan.length > 0 && (
                                <div className="mt-3.5 pt-3 border-t border-border-subtle/30 space-y-1.5">
                                  <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider">
                                    Research Checklist
                                  </span>
                                  <div className="space-y-1">
                                    {msg.researchPlan.map((topic, tIdx) => {
                                      // Tick complete steps
                                      let isDone = false;
                                      if (msg.statusMessage === "synthesizing") {
                                        isDone = true;
                                      } else if (msg.statusMessage === "searching") {
                                        const currentStep = parseInt(msg.statusQuery?.match(/Step (\d)/)?.[1] || "1");
                                        if (tIdx + 2 < currentStep) {
                                          isDone = true;
                                        }
                                      }
                                      return (
                                        <div key={tIdx} className="flex items-center gap-2 text-xs">
                                          <div className={cn(
                                            "w-3.5 h-3.5 rounded-full border flex items-center justify-center flex-shrink-0 text-[8px]",
                                            isDone 
                                              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400 font-bold" 
                                              : "border-border-subtle bg-surface-secondary/40 text-text-muted"
                                          )}>
                                            {isDone ? "✓" : tIdx + 1}
                                          </div>
                                          <span className={cn(
                                            "truncate max-w-[280px]",
                                            isDone ? "text-text-muted/60 line-through" : "text-text-muted"
                                          )}>
                                            {topic}
                                          </span>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          {msg.status === "sending" && actualContent === "" ? (
                            <ThinkingIndicator />
                          ) : msg.status === "error" ? (
                            <div className="flex flex-col gap-3 p-4 rounded-xl border border-rose-500/20 bg-rose-500/5 text-rose-200">
                              <div className="flex items-center gap-2 text-xs font-semibold">
                                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                                Connection or Generation Error
                              </div>
                              <p className="text-xs">{actualContent || "Failed to retrieve a response from NOVA AI."}</p>
                              <button
                                onClick={() => onRegenerateMessage(msg.id)}
                                className="w-fit flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/25 text-[11px] font-bold text-rose-300 hover:text-white transition-all cursor-pointer"
                              >
                                <RotateCcw className="w-3 h-3" />
                                Retry Response
                              </button>
                            </div>
                          ) : (
                            <>
                              {(() => {
                                const imageInfo = msg.imageUrl
                                  ? { imageUrl: msg.imageUrl, prompt: msg.imagePrompt }
                                  : (() => {
                                      const match = actualContent.match(/!\[(?:AI Image:\s*)?(.*?)\]\((https?:\/\/[^\s\)]+)\)/);
                                      return match ? { prompt: match[1] || "AI Image", imageUrl: match[2] } : null;
                                    })();

                                if (imageInfo) {
                                  return (
                                    <ImageMessage
                                      imageUrl={imageInfo.imageUrl}
                                      prompt={imageInfo.prompt}
                                      isLoading={msg.isStreaming && !imageInfo.imageUrl}
                                      onOpenModal={(url, prompt) => setActiveModalImage({ url, prompt })}
                                      onDownload={(url, filename) => downloadImage(url, filename)}
                                    />
                                  );
                                }

                                return <MarkdownRenderer content={actualContent} />;
                              })()}
                              {msg.isStreaming && (
                                <span className="inline-block w-1.5 h-4.5 bg-accent ml-1 align-middle animate-pulse rounded-full" />
                              )}
                              {isAssistant && msg.sources && msg.sources.length > 0 && (
                                <div className="mt-3.5 pt-2.5 border-t border-white/5 flex flex-wrap items-center gap-1.5 select-none">
                                  <span className="text-[10px] font-bold text-white/30 uppercase tracking-wider mr-1 mt-0.5">Sources:</span>
                                  {msg.sources.map((src) => (
                                    <button
                                      key={src.index}
                                      onClick={() => onOpenCitations?.(msg.sources || [], src.index)}
                                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/5 hover:bg-emerald-500/10 border border-emerald-500/15 text-[10px] font-semibold text-emerald-400 hover:text-emerald-300 transition cursor-pointer"
                                    >
                                      <span className="font-bold">[{src.index}]</span>
                                      <span className="truncate max-w-[120px]">{src.filename}</span>
                                    </button>
                                  ))}
                                </div>
                              )}
                              {isAssistant && msg.toolActivity && msg.toolActivity.length > 0 && (
                                <ToolActivity activity={msg.toolActivity} />
                              )}
                              {isAssistant && msg.codeResult && (
                                <CodeExecutionResult result={msg.codeResult} />
                              )}
                            </>
                          )}
                        </div>

                        {/* Hover Pen Edit Icon for User Messages */}
                        {!isAssistant && !isEditing && (
                          <button
                            onClick={() => startEditing(msg)}
                            className="absolute right-full top-1/2 -translate-y-1/2 mr-2 p-1.5 rounded-lg border border-transparent hover:border-border-subtle bg-surface-primary/60 hover:bg-surface-secondary text-text-muted opacity-0 group-hover/msg:opacity-100 transition-all cursor-pointer"
                            title="Edit message"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    )}

                    {/* Actions tray under Assistant Response */}
                    {isAssistant && msg.status !== "sending" && !msg.isStreaming && (
                      <div className="flex items-center gap-1.5 mt-2 px-1 select-none opacity-0 group-hover/msg:opacity-100 focus-within:opacity-100 transition-opacity duration-300 md:duration-200 w-full justify-start">
                        {/* Copy button */}
                        <button
                          onClick={() => handleCopy(msg.id, actualContent)}
                          className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-secondary transition-all cursor-pointer"
                          title="Copy message text"
                        >
                          {copiedId === msg.id ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                        {/* Regenerate button */}
                        <button
                          onClick={() => onRegenerateMessage(msg.id)}
                          className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-secondary transition-all cursor-pointer"
                          title="Regenerate reply"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                        </button>
                        {/* Rate Up */}
                        <button
                          onClick={() => handleRate(msg.id, "up")}
                          className={cn(
                            "p-1.5 rounded-lg transition-all cursor-pointer",
                            isRatedUp
                              ? "text-accent bg-accent/5 border border-accent/15"
                              : "text-text-muted hover:text-text-primary hover:bg-surface-secondary"
                          )}
                          title="Rate positive"
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                        </button>
                        {/* Rate Down */}
                        <button
                          onClick={() => handleRate(msg.id, "down")}
                          className={cn(
                            "p-1.5 rounded-lg transition-all cursor-pointer",
                            isRatedDown
                              ? "text-red-400 bg-red-400/5 border border-red-400/15"
                              : "text-text-muted hover:text-text-primary hover:bg-surface-secondary"
                          )}
                          title="Rate negative"
                        >
                          <ThumbsDown className="w-3.5 h-3.5" />
                        </button>

                        {/* More Options Popover */}
                        <div className="relative">
                          <button
                            onClick={() =>
                              setActiveMenuId(activeMenuId === msg.id ? null : msg.id)
                            }
                            className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-secondary transition-all cursor-pointer"
                            title="More actions"
                          >
                            <MoreHorizontal className="w-3.5 h-3.5" />
                          </button>

                          {activeMenuId === msg.id && (
                            <div className="absolute left-0 bottom-full mb-2 w-44 bg-surface-primary border border-border-subtle rounded-xl shadow-xl glass-panel p-1 z-30 animate-in fade-in slide-in-from-bottom-1 duration-150">
                              <button
                                onClick={() => {
                                  handleCopy(msg.id + "-raw", msg.content);
                                  setActiveMenuId(null);
                                }}
                                className="w-full flex items-center gap-2 p-2 text-left rounded-lg text-xs text-text-muted hover:text-text-primary hover:bg-surface-secondary"
                              >
                                <Eye className="w-3.5 h-3.5" />
                                <span>Copy Raw Markdown</span>
                              </button>
                              {onDeleteMessage && (
                                <button
                                  onClick={() => {
                                    onDeleteMessage(msg.id);
                                    setActiveMenuId(null);
                                  }}
                                  className="w-full flex items-center gap-2 p-2 text-left rounded-lg text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                  <span>Delete Message</span>
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            <div ref={messagesEndRef} className="h-2" />
          </div>
        </div>
      )}

      {/* Floating snap scroll bottom indicator */}
      {showScrollBottomBtn && (
        <button
          onClick={() => scrollToBottom()}
          className="absolute bottom-28 right-8 flex items-center gap-1.5 px-3.5 py-2 rounded-full border border-border-subtle bg-surface-primary/95 hover:bg-surface-secondary text-[10px] font-bold text-text-primary uppercase tracking-wider shadow-2xl hover:scale-105 active:scale-95 transition-all z-20 backdrop-blur-md cursor-pointer animate-in fade-in slide-in-from-bottom-2 duration-200"
        >
          <ArrowDown className="w-3.5 h-3.5 text-accent animate-bounce" />
          <span>{isLoading ? "New response" : "Scroll to bottom"}</span>
        </button>
      )}

      {/* Floating Chat Input Bar */}
      <ChatInput
        value={inputVal}
        onChange={handleInputChange}
        onSubmit={handleSend}
        isLoading={isLoading}
        onStop={onStopGeneration}
        attachments={attachments}
        onAddAttachments={onAddAttachments}
        onRemoveAttachment={onRemoveAttachment}
        selectedTool={selectedTool}
        onSelectTool={onSelectTool}
        onAttachClick={onAttachClick}
        onUploadComplete={onUploadComplete}
      />

      {/* AI Image Full Screen Modal */}
      <ImageViewerModal
        isOpen={!!activeModalImage}
        imageUrl={activeModalImage?.url || ""}
        prompt={activeModalImage?.prompt}
        onClose={() => setActiveModalImage(null)}
        onDownload={(url, filename) => downloadImage(url, filename)}
      />
    </div>
  );
}
