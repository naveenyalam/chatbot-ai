"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { MainLayout } from "@/components/layout/MainLayout";
import { ChatArea } from "@/components/chat/ChatArea";
import { DashboardOverview } from "@/components/dashboard/DashboardOverview";
import { AgentWorkspace } from "@/components/agents/AgentWorkspace";
import { ConfirmationModal } from "@/components/ui/ConfirmationModal";
import { Chat, Message, Attachment, User, WorkspaceView } from "@/types";
import { streamChatResponse } from "@/lib/api/chat";
import { StreamController } from "@/lib/ai/types";
import { ToolType } from "@/components/chat/ChatInput";
import { getMe, logoutUser } from "@/lib/api/auth";
import { onSessionExpired } from "@/lib/api/client";
import {
  listConversations,
  listMessages,
  deleteConversation,
  renameConversation,
  deleteMessage as deleteMessageApi,
  generateConversationTitle,
} from "@/lib/api/conversations";
import { DocumentLibrary } from "@/components/documents/DocumentLibrary";
import { CollectionsView } from "@/components/documents/CollectionsView";
import { ResearchWorkspace } from "@/components/workspaces/ResearchWorkspace";
import { CodingWorkspace as DevWorkspace } from "@/components/workspaces/CodingWorkspace";
import { DataAnalysisWorkspace } from "@/components/workspaces/DataAnalysisWorkspace";
import { PromptLibrary } from "@/components/productivity/PromptLibrary";
import { ChatTemplates } from "@/components/productivity/ChatTemplates";
import { SavedResponses } from "@/components/productivity/SavedResponses";
import { SourcePanel, CitationSource } from "@/components/chat/SourcePanel";
import { useApp } from "@/components/providers/ThemeProvider";
import { useToast } from "@/components/ui/Toast";
import { listDocuments, DocumentResponse } from "@/lib/api/documents";
import { Sparkles } from "lucide-react";

const generateId = (prefix: string) => {
  if (typeof window !== "undefined" && window.crypto && window.crypto.randomUUID) {
    return `${prefix}-${window.crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 1000000)}`;
};
const getIsoString = () => new Date().toISOString();

export default function Home() {
  const { settings } = useApp();
  const router = useRouter();
  const toast = useToast();
  
  // Auth state
  const [user, setUser] = useState<User | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  const hasHandledSessionExpiryRef = useRef(false);
  const sessionCheckInFlightRef = useRef(false);
  const isCheckingAuthRef = useRef(isCheckingAuth);
  const userRef = useRef(user);

  useEffect(() => {
    isCheckingAuthRef.current = isCheckingAuth;
  }, [isCheckingAuth]);

  useEffect(() => {
    userRef.current = user;
  }, [user]);

  // Global 401 Session Expiration Listener
  useEffect(() => {
    const unsubscribe = onSessionExpired(() => {
      if (!hasHandledSessionExpiryRef.current) {
        hasHandledSessionExpiryRef.current = true;
        setUser(null);
        toast.error("Your session has expired. Redirecting to login...");
        router.push("/login");
      }
    });
    return unsubscribe;
  }, [router, toast]);

  const checkSession = async (force = false) => {
    if (sessionCheckInFlightRef.current && !force) return;
    sessionCheckInFlightRef.current = true;
    setAuthError(null);

    const checkWithTimeout = Promise.race([
      getMe(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Session check timeout")), 3500)
      ),
    ]);

    try {
      const dbUser = (await checkWithTimeout) as any;
      setUser({
        name: dbUser.name,
        email: dbUser.email,
        avatarUrl: dbUser.avatar_url || undefined,
        plan: "Enterprise",
      });
      setIsCheckingAuth(false);
    } catch (err: any) {
      const isNetworkError = err.message === "Failed to fetch" || err.message?.includes("NetworkError") || err.message?.includes("Failed to connect");
      setIsCheckingAuth(false);
      if (isNetworkError) {
        setAuthError("Unable to connect to NOVA. Check that the NOVA backend is running.");
      } else if (err.message === "Session check timeout") {
        // Render backend is cold-starting or session not active; gracefully unblock UI
        setUser(null);
      } else {
        setUser(null);
        if (!hasHandledSessionExpiryRef.current) {
          hasHandledSessionExpiryRef.current = true;
          toast.error("Your session has expired. Redirecting to login...");
          router.push("/login");
        }
      }
    } finally {
      sessionCheckInFlightRef.current = false;
    }
  };

  // Application workspace state
  const [activeView, setActiveView] = useState<WorkspaceView>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("nova_active_workspace") as WorkspaceView;
      const validViews: WorkspaceView[] = [
        "chat", "research", "writing", "code", "documents",
        "data", "agents", "collections", "prompts", "templates",
        "saved", "dashboard", "settings"
      ];
      if (saved && validViews.includes(saved)) {
        return saved;
      }
    }
    return "chat";
  });

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("nova_active_workspace", activeView);
    }
  }, [activeView]);

  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("nova_selected_model") || "intelligence";
    }
    return "intelligence";
  });

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("nova_selected_model", selectedModel);
    }
  }, [selectedModel]);

  const [selectedTool, setSelectedTool] = useState<ToolType | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  // Deletion modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [chatToDeleteId, setChatToDeleteId] = useState<string | null>(null);

  // Layout UI states
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // Document Library & Citations RAG states
  const [isDocLibraryOpen, setIsDocLibraryOpen] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [isSourcePanelOpen, setIsSourcePanelOpen] = useState(false);
  const [activeCitations, setActiveCitations] = useState<CitationSource[]>([]);
  const [highlightedCitationIndex, setHighlightedCitationIndex] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (isCheckingAuth || !user) return;
    listDocuments()
      .then(setDocuments)
      .catch((err) => console.error("Error loading document catalog:", err));
  }, [isCheckingAuth, user]);

  const streamControllerRef = useRef<StreamController | null>(null);

  // 1. Session verification and periodic polling guard
  useEffect(() => {
    checkSession();

    // 10 seconds timeout for initial check
    const timeout = setTimeout(() => {
      if (isCheckingAuthRef.current && !userRef.current && !sessionCheckInFlightRef.current) {
        setAuthError("Unable to connect to NOVA. Check that the NOVA backend is running.");
      }
    }, 10000);

    // Poll session status every 60 seconds
    const interval = setInterval(() => {
      if (!isCheckingAuthRef.current && userRef.current && !hasHandledSessionExpiryRef.current) {
        checkSession();
      }
    }, 60000);

    return () => {
      clearTimeout(timeout);
      clearInterval(interval);
    };
  }, [router]);

  // 2. Fetch conversations on successful login validation
  useEffect(() => {
    if (isCheckingAuth || !user) return;
    loadConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isCheckingAuth, user]);

  async function loadConversations() {
    try {
      const list = await listConversations();
      setChats((prevChats) => {
        return list.map((c) => {
          const existing = prevChats.find((exist) => exist.id === c.id);
          return {
            id: c.id,
            title: c.title,
            createdAt: c.created_at,
            messages: existing ? existing.messages : [],
          };
        });
      });

      if (list.length > 0 && !activeChatId) {
        handleSelectChat(list[0].id);
      }
    } catch (err) {
      console.error("Failed to load user conversations:", err);
    }
  }

  const messagesFetchControllerRef = useRef<AbortController | null>(null);

  const handleSelectChat = async (id: string) => {
    if (isLoading) handleStopGeneration(activeChatId || undefined);

    // Cancel in-flight message fetch
    if (messagesFetchControllerRef.current) {
      messagesFetchControllerRef.current.abort();
    }
    const controller = new AbortController();
    messagesFetchControllerRef.current = controller;

    setActiveChatId(id);
    setSidebarOpen(false);
    setSelectedDocIds([]);

    try {
      const msgs = await listMessages(id, controller.signal);
      setChats((prev) =>
        prev.map((c) => (c.id === id ? { ...c, messages: msgs } : c))
      );
    } catch (err: any) {
      if (err.name === "AbortError" || controller.signal.aborted) {
        return;
      }
      console.error("Failed to fetch messages for conversation:", id, err);
      toast.error("Conversation could not be loaded");
      setChats((prev) => prev.filter((c) => c.id !== id));
      setActiveChatId(null);
    } finally {
      if (messagesFetchControllerRef.current === controller) {
        messagesFetchControllerRef.current = null;
      }
    }
  };

  const handleNewChat = () => {
    if (isLoading) handleStopGeneration(activeChatId || undefined);
    setActiveChatId(null);
    setSelectedDocIds([]);
    setActiveView("chat");
  };

  const handleDeleteChatTrigger = (id: string) => {
    setChatToDeleteId(id);
    setDeleteModalOpen(true);
  };

  const handleConfirmDeleteChat = async () => {
    if (!chatToDeleteId) return;
    try {
      await deleteConversation(chatToDeleteId);
      const updated = chats.filter((c) => c.id !== chatToDeleteId);
      setChats(updated);
      toast.success("Conversation deleted");

      if (activeChatId === chatToDeleteId) {
        if (updated.length > 0) {
          handleSelectChat(updated[0].id);
        } else {
          setActiveChatId(null);
        }
      }
    } catch (err) {
      toast.error("Failed to delete conversation");
      console.error("Failed to delete conversation:", err);
    } finally {
      setChatToDeleteId(null);
      setDeleteModalOpen(false);
    }
  };

  const handleRenameChat = async (id: string, newTitle: string) => {
    try {
      await renameConversation(id, newTitle);
      setChats((prev) =>
        prev.map((c) => (c.id === id ? { ...c, title: newTitle } : c))
      );
      toast.success("Conversation renamed");
    } catch (err) {
      toast.error("Failed to rename conversation");
      console.error("Failed to rename conversation:", err);
    }
  };

  const handleDuplicateChat = async (id: string) => {
    const chatToDuplicate = chats.find((c) => c.id === id);
    if (!chatToDuplicate) return;

    try {
      await renameConversation(id, `${chatToDuplicate.title} (Copy)`);
      loadConversations();
      toast.info("Conversation duplicated");
    } catch (err) {
      toast.error("Failed to duplicate conversation");
      console.error("Failed to duplicate chat:", err);
    }
  };

  const handleClearChats = async () => {
    if (isLoading) handleStopGeneration(activeChatId || undefined);
    try {
      for (const c of chats) {
        await deleteConversation(c.id);
      }
      setChats([]);
      setActiveChatId(null);
      toast.info("All conversations cleared");
    } catch (err) {
      toast.error("Failed to clear conversations");
      console.error("Failed to clear chat lists:", err);
    }
  };

  const executeResponseStream = (
    promptText: string,
    history: Message[],
    targetChatId: string,
    docIdsToPass?: string[]
  ) => {
    if (streamControllerRef.current) {
      streamControllerRef.current.stop();
    }

    setIsLoading(true);

    const targetIdRef = { current: targetChatId };

    const assistantMsgId = generateId("msg");
    const initialAssistantMsg: Message = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      timestamp: getIsoString(),
      status: "sending" as const,
      isStreaming: true,
    };

    setChats((prev) =>
      prev.map((c) =>
        c.id === targetIdRef.current
          ? { ...c, messages: [...c.messages, initialAssistantMsg] }
          : c
      )
    );

    const backendConvId = targetIdRef.current.startsWith("temp-") ? undefined : targetIdRef.current;

    const controller = streamChatResponse(history, {
      model: selectedModel,
      conversation_id: backendConvId,
      document_ids: docIdsToPass || (selectedDocIds.length > 0 ? selectedDocIds : undefined),
      mode: selectedTool || activeView || "chat",
      response_style: settings.responseStyle,
      response_tone: settings.responseTone,
      semantic_chunk_limit: settings.semanticChunkLimit,
      similarity_filtering: settings.similarityFiltering,
      language: settings.language,
      onSources: (sources) => {
        setChats((prevChats) =>
          prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsgId ? { ...m, sources } : m
                  ),
                }
              : c
          )
        );
      },
      onStatusChange: (status, query) => {
        setChats((prevChats) =>
          prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsgId ? { ...m, statusMessage: status, statusQuery: query } : m
                  ),
                }
              : c
          )
        );
      },
      onResearchPlan: (subtopics) => {
        setChats((prevChats) =>
          prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsgId ? { ...m, researchPlan: subtopics } : m
                  ),
                }
              : c
          )
        );
      },
      onAgentStart: (agent, label) => {
        setChats((prevChats) =>
          prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsgId ? { ...m, agentType: agent, toolActivity: [] } : m
                  ),
                }
              : c
          )
        );
      },
      onToolStart: (tool, label) => {
        setChats((prevChats) =>
          prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) => {
                    if (m.id !== assistantMsgId) return m;
                    const prevActivity = m.toolActivity || [];
                    return {
                      ...m,
                      toolActivity: [...prevActivity, { tool, label, status: "running" as const }],
                    };
                  }),
                }
              : c
          )
        );
      },
      onToolResult: (tool, success, data, label, error) => {
        setChats((prevChats) =>
          prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) => {
                    if (m.id !== assistantMsgId) return m;
                    const prevActivity = m.toolActivity || [];
                    const updated = prevActivity.map((act) => {
                      if (act.tool === tool && act.status === "running") {
                        return {
                          ...act,
                          status: (success ? "complete" : "failed") as "complete" | "failed",
                          data,
                          error,
                          preview: typeof data === "object" ? JSON.stringify(data) : String(data),
                        };
                      }
                      return act;
                    });
                    return {
                      ...m,
                      toolActivity: updated,
                    };
                  }),
                }
              : c
          )
        );
      },
      onCodeResult: (data) => {
        setChats((prevChats) =>
          prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsgId
                      ? {
                          ...m,
                          codeResult: {
                            language: data.language || "python",
                            stdout: data.stdout || "",
                            stderr: data.stderr || "",
                            exit_code: data.exit_code,
                            execution_time: data.execution_time,
                          },
                        }
                      : m
                  ),
                }
              : c
          )
        );
      },
      onAgentComplete: (toolActivity) => {
        setChats((prevChats) =>
          prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) => {
                    if (m.id !== assistantMsgId) return m;
                    const mappedActivity = (toolActivity || []).map((a: any) => ({
                      tool: a.tool,
                      label: a.label,
                      status: (a.status === "success" ? "complete" : a.status) as any,
                      duration: a.duration,
                      preview: a.result_preview,
                    }));
                    return {
                      ...m,
                      toolActivity: mappedActivity,
                    };
                  }),
                }
              : c
          )
        );
      },
      onConversationCreated: (newRealId) => {
        const oldId = targetIdRef.current;
        targetIdRef.current = newRealId;
        setChats((prev) =>
          prev.map((c) => (c.id === oldId ? { ...c, id: newRealId } : c))
        );
        setActiveChatId(newRealId);
      },
      onChunk: (chunk) => {
        setChats((prevChats) =>
          prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsgId
                      ? {
                          ...m,
                          content: chunk,
                          status: "streaming" as const,
                          isStreaming: true,
                        }
                      : m
                  ),
                }
              : c
          )
        );
      },
      onComplete: (fullText) => {
        setIsLoading(false);
        setChats((prevChats) => {
          const finalChats = prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsgId
                      ? {
                          ...m,
                          content: fullText,
                          status: "complete" as const,
                          isStreaming: false,
                        }
                      : m
                  ),
                }
              : c
          );
          return finalChats;
        });
        streamControllerRef.current = null;
        if (targetIdRef.current && !targetIdRef.current.startsWith("temp-")) {
          generateConversationTitle(targetIdRef.current)
            .then((updated) => {
              if (updated && updated.title) {
                setChats((prev) =>
                  prev.map((c) => (c.id === updated.id ? { ...c, title: updated.title } : c))
                );
              }
            })
            .catch(() => {});
        }
        loadConversations();
      },
      onError: (err) => {
        setIsLoading(false);
        const friendlyMessage = err.message.includes("AI provider") || err.message.includes("not configured")
          ? err.message
          : err.message.includes("401") || err.message.includes("403")
          ? "Your session has expired. Please sign in again."
          : err.message.includes("Failed to fetch") || err.message.includes("NetworkError")
          ? "Unable to connect to NOVA AI. Check your connection and try again."
          : "NOVA couldn't complete this response. Please try again.";

        toast.error(friendlyMessage);

        setChats((prevChats) => {
          const finalChats = prevChats.map((c) =>
            c.id === targetIdRef.current
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsgId
                      ? {
                          ...m,
                          content: m.content ? m.content + `\n\n[${friendlyMessage}]` : friendlyMessage,
                          status: "error" as const,
                          isStreaming: false,
                        }
                      : m
                  ),
                }
              : c
          );
          return finalChats;
        });
        streamControllerRef.current = null;
        loadConversations();
      },
    });

    streamControllerRef.current = controller;
  };

  const handleUploadComplete = (doc: DocumentResponse) => {
    setDocuments((prev) => {
      if (prev.some((d) => d.id === doc.id)) return prev;
      return [...prev, doc];
    });
    setSelectedDocIds((prev) => {
      if (prev.includes(doc.id)) return prev;
      return [...prev, doc.id];
    });
  };

  const attachedFiles = selectedDocIds.map((id) => {
    const doc = documents.find((d) => d.id === id);
    if (!doc) return null;
    return {
      id: doc.id,
      name: doc.original_filename,
      size: doc.file_size,
      type: doc.mime_type,
      status: "ready" as const,
      progress: 100,
    };
  }).filter(Boolean) as Attachment[];

  const combinedAttachments = [
    ...attachedFiles,
    ...attachments.filter((a) => !selectedDocIds.includes(a.id)),
  ];

  const handleSendMessage = (content: string) => {
    if (isLoading) return;
    setActiveView("chat");

    const currentDocIds = [...selectedDocIds];
    const currentAttachments = [...combinedAttachments];

    const userMsg: Message = {
      id: generateId("msg"),
      role: "user",
      content,
      timestamp: getIsoString(),
      status: "complete",
      attachments: currentAttachments.length > 0 ? currentAttachments : undefined,
    };

    setAttachments([]);
    setSelectedDocIds([]);

    let targetId = activeChatId;
    let newHistory: Message[] = [];

    if (!targetId) {
      const tempId = generateId("temp");
      const tempChat: Chat = {
        id: tempId,
        title: content.length > 25 ? `${content.substring(0, 23)}...` : content,
        createdAt: getIsoString(),
        messages: [userMsg],
      };
      setChats((prev) => [tempChat, ...prev]);
      setActiveChatId(tempId);
      targetId = tempId;
      newHistory = [userMsg];
    } else {
      const currentChat = chats.find((c) => c.id === targetId);
      if (!currentChat) return;
      newHistory = [...currentChat.messages, userMsg];
      setChats((prev) =>
        prev.map((c) => (c.id === targetId ? { ...c, messages: newHistory } : c))
      );
    }

    executeResponseStream(content, newHistory, targetId, currentDocIds);
  };

  const handleEditMessage = (msgId: string, newContent: string) => {
    if (isLoading || !activeChatId) return;

    const currentChat = chats.find((c) => c.id === activeChatId);
    if (!currentChat) return;

    const msgIndex = currentChat.messages.findIndex((m) => m.id === msgId);
    if (msgIndex === -1) return;

    const updatedMessages = currentChat.messages.slice(0, msgIndex);
    const editedUserMsg = {
      ...currentChat.messages[msgIndex],
      content: newContent,
      timestamp: getIsoString(),
    };

    const newHistory = [...updatedMessages, editedUserMsg];
    const updatedChats = chats.map((c) =>
      c.id === activeChatId ? { ...c, messages: newHistory } : c
    );
    setChats(updatedChats);

    executeResponseStream(newContent, newHistory, activeChatId);
  };

  const handleRegenerateMessage = (msgId: string) => {
    if (isLoading || !activeChatId) return;

    const currentChat = chats.find((c) => c.id === activeChatId);
    if (!currentChat) return;

    const msgIndex = currentChat.messages.findIndex((m) => m.id === msgId);
    if (msgIndex === -1) return;

    const precedingUserMsg = currentChat.messages
      .slice(0, msgIndex)
      .reverse()
      .find((m) => m.role === "user");

    if (!precedingUserMsg) return;

    const userMsgIndex = currentChat.messages.indexOf(precedingUserMsg);
    const truncatedHistory = currentChat.messages.slice(0, userMsgIndex + 1);

    const updatedChats = chats.map((c) =>
      c.id === activeChatId ? { ...c, messages: truncatedHistory } : c
    );
    setChats(updatedChats);

    executeResponseStream(precedingUserMsg.content, truncatedHistory, activeChatId);
  };

  const handleStopGeneration = (chatIdToStop?: string) => {
    const targetId = chatIdToStop || activeChatId;
    if (streamControllerRef.current) {
      streamControllerRef.current.stop();
      setIsLoading(false);

      if (targetId) {
        setChats((prevChats) => {
          const finalChats = prevChats.map((c) =>
            c.id === targetId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.isStreaming
                      ? {
                          ...m,
                          status: "stopped" as const,
                          isStreaming: false,
                        }
                      : m
                  ),
                }
              : c
          );
          return finalChats;
        });
      }

      streamControllerRef.current = null;
    }
  };

  const handleSignOut = async () => {
    try {
      await logoutUser();
      setUser(null);
      router.push("/login");
    } catch (err) {
      console.error("Logout request failed:", err);
      setUser(null);
      router.push("/login");
    }
  };

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-[#070A12] flex flex-col items-center justify-center relative overflow-hidden text-zinc-100 p-6 select-none">
        {/* Subtle Background Orb */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full bg-indigo-500/5 blur-[100px] pointer-events-none" />
        
        <div className="flex flex-col items-center gap-6 relative z-10 text-center max-w-sm">
          {/* Logo Emblem */}
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-xl shadow-indigo-500/25">
            <div className="w-full h-full bg-[#0b0f19] rounded-[14px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-indigo-400" />
            </div>
          </div>
          
          <div className="space-y-1">
            <h1 className="text-lg font-black tracking-widest text-white uppercase">NOVA AI</h1>
            <p className="text-zinc-500 text-[10px] tracking-wider uppercase font-bold">Platform OS v10.0</p>
          </div>

          {authError ? (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs leading-relaxed max-w-xs mx-auto">
                {authError}
              </div>
              <button
                onClick={() => checkSession(true)}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20 active:scale-[0.98] transition-all cursor-pointer"
              >
                Retry Connection
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <span className="text-zinc-400 text-xs font-semibold tracking-wide">
                Loading your workspace
              </span>
              <div className="flex items-center gap-1.5 justify-center py-2">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.3s]" />
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.15s]" />
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" />
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  const activeChat = chats.find((c) => c.id === activeChatId) || null;

  const handleExportChat = (format: "md" | "json" | "txt") => {
    if (!activeChat) return;

    let content = "";
    let mimeType = "text/plain";
    let extension = "txt";

    if (format === "md") {
      mimeType = "text/markdown";
      extension = "md";
      content = `# ${activeChat.title}\n\n*Exported from NOVA AI on ${new Date().toLocaleString()}*\n\n---\n\n`;
      activeChat.messages.forEach((m) => {
        content += `### ${m.role === "user" ? "User" : "NOVA AI"} (${new Date(m.timestamp).toLocaleTimeString()})\n\n${m.content}\n\n`;
        if (m.sources && m.sources.length > 0) {
          content += `**Sources:**\n`;
          m.sources.forEach((s) => {
            content += `- [${s.index}] ${s.filename}\n`;
          });
          content += `\n`;
        }
      });
    } else if (format === "json") {
      mimeType = "application/json";
      extension = "json";
      content = JSON.stringify(
        {
          id: activeChat.id,
          title: activeChat.title,
          model: activeChat.model,
          exported_at: new Date().toISOString(),
          messages: activeChat.messages,
        },
        null,
        2
      );
    } else {
      content = `TITLE: ${activeChat.title}\nEXPORTED: ${new Date().toLocaleString()}\n\n`;
      activeChat.messages.forEach((m) => {
        content += `[${m.role.toUpperCase()}] ${m.content}\n\n`;
      });
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${activeChat.title.replace(/[^a-z0-9]/gi, "_").toLowerCase()}_export.${extension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`Exported conversation as ${extension.toUpperCase()}`);
  };

  const handleDeleteMessage = async (msgId: string) => {
    if (!activeChatId) return;
    try {
      setChats((prev) =>
        prev.map((c) => {
          if (c.id === activeChatId) {
            return {
              ...c,
              messages: c.messages.filter((m) => m.id !== msgId),
            };
          }
          return c;
        })
      );
      if (!activeChatId.startsWith("temp-")) {
        await deleteMessageApi(activeChatId, msgId);
      }
      toast.success("Message deleted");
    } catch (err) {
      console.error("Failed to delete message:", err);
      toast.error("Failed to delete message");
    }
  };

  return (
    <>
      <MainLayout
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        settingsOpen={settingsOpen}
        setSettingsOpen={setSettingsOpen}
        commandPaletteOpen={commandPaletteOpen}
        setCommandPaletteOpen={setCommandPaletteOpen}
        activeView={activeView}
        onChangeView={setActiveView}
        chats={chats}
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChatTrigger}
        onRenameChat={handleRenameChat}
        onDuplicateChat={handleDuplicateChat}
        onClearChats={handleClearChats}
        onSignOut={handleSignOut}
        user={user}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        onExportChat={handleExportChat}
      >
        {activeView === "dashboard" && (
          <DashboardOverview
            user={user}
            chats={chats}
            documents={documents}
            onNewChat={handleNewChat}
            onOpenDocuments={() => setActiveView("documents")}
            onOpenAgents={() => setActiveView("agents")}
            onOpenCode={() => setActiveView("code")}
          />
        )}

        {activeView === "chat" && (
          <ChatArea
            activeChat={activeChat}
            onSendMessage={handleSendMessage}
            onEditMessage={handleEditMessage}
            onRegenerateMessage={handleRegenerateMessage}
            onStopGeneration={() => handleStopGeneration()}
            onDeleteMessage={handleDeleteMessage}
            isLoading={isLoading}
            activeView={activeView}
            selectedModel={selectedModel}
            selectedDocIds={selectedDocIds}
            documents={documents}
            attachments={attachments}
            onAddAttachments={setAttachments}
            onRemoveAttachment={(id) =>
              setAttachments((prev) => prev.filter((a) => a.id !== id))
            }
            selectedTool={selectedTool}
            onSelectTool={setSelectedTool}
            onAttachClick={() => setIsDocLibraryOpen(true)}
            onOpenCitations={(sources, idx) => {
              setActiveCitations(sources);
              setHighlightedCitationIndex(idx);
              setIsSourcePanelOpen(true);
            }}
            onUploadComplete={handleUploadComplete}
          />
        )}

        {activeView === "documents" && (
          <div className="flex-1 p-6 md:p-8 max-w-6xl mx-auto w-full overflow-y-auto">
            <DocumentLibrary
              isOpen={true}
              onClose={() => setActiveView("chat")}
              selectedDocIds={selectedDocIds}
              onToggleSelectDoc={(docId) => {
                setSelectedDocIds((prev) =>
                  prev.includes(docId)
                    ? prev.filter((id) => id !== docId)
                    : [...prev, docId]
                );
              }}
              documents={documents}
              setDocuments={setDocuments}
            />
          </div>
        )}

        {activeView === "collections" && <CollectionsView />}

        {activeView === "research" && <ResearchWorkspace />}

        {activeView === "writing" && (
          <ChatArea
            activeChat={activeChat}
            onSendMessage={handleSendMessage}
            onEditMessage={handleEditMessage}
            onRegenerateMessage={handleRegenerateMessage}
            onStopGeneration={() => handleStopGeneration()}
            onDeleteMessage={handleDeleteMessage}
            isLoading={isLoading}
            activeView="writing"
            selectedModel={selectedModel}
            selectedDocIds={selectedDocIds}
            documents={documents}
            attachments={attachments}
            onAddAttachments={setAttachments}
            onRemoveAttachment={(id) =>
              setAttachments((prev) => prev.filter((a) => a.id !== id))
            }
            selectedTool={selectedTool}
            onSelectTool={setSelectedTool}
            onAttachClick={() => setIsDocLibraryOpen(true)}
            onOpenCitations={(sources, idx) => {
              setActiveCitations(sources);
              setHighlightedCitationIndex(idx);
              setIsSourcePanelOpen(true);
            }}
            onUploadComplete={handleUploadComplete}
          />
        )}

        {activeView === "code" && <DevWorkspace />}

        {activeView === "data" && <DataAnalysisWorkspace />}

        {activeView === "agents" && (
          <AgentWorkspace
            onLaunchAgentTask={(prompt: string, tool: ToolType) => {
              handleNewChat();
              setSelectedTool(tool);
              setActiveView("chat");
              handleSendMessage(prompt);
            }}
          />
        )}

        {activeView === "prompts" && (
          <PromptLibrary
            onInsertPrompt={(content: string) => {
              handleNewChat();
              setActiveView("chat");
              handleSendMessage(content);
            }}
          />
        )}

        {activeView === "templates" && (
          <ChatTemplates
            onInsertTemplate={(content: string) => {
              handleNewChat();
              setActiveView("chat");
              handleSendMessage(content);
            }}
          />
        )}

        {activeView === "saved" && <SavedResponses />}
      </MainLayout>

      <ConfirmationModal
        isOpen={deleteModalOpen}
        title="Delete Conversation"
        message="Are you sure you want to delete this conversation? All associated messages and response history will be permanently deleted."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        onConfirm={handleConfirmDeleteChat}
        onClose={() => setDeleteModalOpen(false)}
      />

      <DocumentLibrary
        isOpen={isDocLibraryOpen}
        onClose={() => setIsDocLibraryOpen(false)}
        selectedDocIds={selectedDocIds}
        onToggleSelectDoc={(docId) => {
          setSelectedDocIds((prev) =>
            prev.includes(docId)
              ? prev.filter((id) => id !== docId)
              : [...prev, docId]
          );
        }}
        documents={documents}
        setDocuments={setDocuments}
      />

      <SourcePanel
        isOpen={isSourcePanelOpen}
        onClose={() => setIsSourcePanelOpen(false)}
        sources={activeCitations}
        highlightIndex={highlightedCitationIndex}
      />
    </>
  );
}
