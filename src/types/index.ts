export type MessageRole = "user" | "assistant" | "system";

export type MessageStatus = "sending" | "streaming" | "complete" | "error" | "stopped";

export interface Attachment {
  id: string;
  name: string;
  size: number;
  type: string;
  status: "uploading" | "ready" | "error";
  progress?: number;
}

export interface CitationSource {
  index: number;
  filename: string;
  page: number;
  content: string;
}

export interface ToolActivityItem {
  tool: string;
  label: string;
  status: "running" | "complete" | "failed";
  duration?: number;
  preview?: string;
  data?: any;
  error?: string;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string; // ISO string
  status?: MessageStatus;
  isStreaming?: boolean;
  messageType?: "text" | "image" | "error";
  imageUrl?: string;
  imagePrompt?: string;
  attachments?: Attachment[];
  sources?: CitationSource[];
  statusMessage?: string;
  statusQuery?: string;
  researchPlan?: string[];
  agentType?: string;
  toolActivity?: ToolActivityItem[];
  codeResult?: {
    language: string;
    stdout: string;
    stderr: string;
    exit_code?: number;
    execution_time?: number;
  };
}


export interface Chat {
  id: string;
  title: string;
  createdAt: string; // ISO string
  messages: Message[];
  model?: string;
}

export interface User {
  name: string;
  email: string;
  avatarUrl?: string;
  plan: "Free Plan" | "Pro Plan" | "Enterprise";
}

export type WorkspaceView =
  | "chat"
  | "research"
  | "writing"
  | "code"
  | "data"
  | "documents"
  | "agents"
  | "collections"
  | "prompts"
  | "templates"
  | "saved"
  | "dashboard"
  | "settings";

export interface Settings {
  theme: "light" | "dark" | "system";
  animationsEnabled: boolean;
  compactMode: boolean;
  soundEffectsEnabled: boolean;
  sendWithEnter: boolean;
  semanticChunkLimit: number;
  similarityFiltering: boolean;
  chatRetention: boolean;
  responseStyle: "concise" | "balanced" | "detailed";
  responseTone: "professional" | "friendly" | "technical";
  language?: "auto" | "en" | "te" | "hi" | "kn" | "ta";
}

