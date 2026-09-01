import { Message } from "@/types";
import { API_URL } from "./client";

export interface StreamChatOptions {
  model?: string;
  temperature?: number;
  conversation_id?: string;
  document_ids?: string[];
  mode?: string;
  onChunk: (chunk: string) => void;
  onSources?: (sources: any[]) => void;
  onStatusChange?: (status: string, query?: string) => void;
  onResearchPlan?: (subtopics: string[]) => void;
  onAgentStart?: (agent: string, label: string) => void;
  onToolStart?: (tool: string, label: string) => void;
  onToolResult?: (tool: string, success: boolean, data: any, label: string, error?: string) => void;
  onCodeResult?: (data: any) => void;
  onAgentComplete?: (toolActivity: any) => void;
  onComplete: (fullText: string) => void;
  onConversationCreated?: (id: string) => void;
  onError: (error: Error) => void;
  signal?: AbortSignal;
  response_style?: string;
  response_tone?: string;
  semantic_chunk_limit?: number;
  similarity_filtering?: boolean;
  language?: string;
}

export async function fetchWorkspaces() {
  const res = await fetch(`${API_URL}/api/workspaces`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch workspaces list");
  return res.json();
}

export async function fetchWorkspaceDetail(workspaceId: string) {
  const res = await fetch(`${API_URL}/api/workspaces/${workspaceId}`, { credentials: "include" });
  if (!res.ok) throw new Error(`Failed to fetch metadata for workspace ${workspaceId}`);
  return res.json();
}

/**
 * Initiates an HTTP POST streaming request to the FastAPI server,
 * decoding server-sent token emissions in real-time.
 */
export function streamChatResponse(
  messages: Message[],
  options: StreamChatOptions
) {
  const controller = new AbortController();
  const signal = options.signal || controller.signal;

  const execute = async () => {
    try {
      // Map standard frontend types to FastAPI validation schema
      const payloadMessages = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const activeMode = (options.mode || "general").toLowerCase();
      const endpoint = `${API_URL}/api/workspaces/${encodeURIComponent(activeMode)}/chat`;

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: payloadMessages,
          message: payloadMessages[payloadMessages.length - 1]?.content || "",
          model: options.model || "nova-intelligence",
          temperature: options.temperature ?? 0.7,
          conversation_id: options.conversation_id,
          document_ids: options.document_ids,
          workspace_mode: activeMode,
          response_style: options.response_style,
          response_tone: options.response_tone,
          semantic_chunk_limit: options.semantic_chunk_limit,
          similarity_filtering: options.similarity_filtering,
          language: options.language,
        }),
        credentials: "include", // Crucial for session cookies exchange
        signal,
      });

      if (!response.ok) {
        let errMessage = `API request failed with code ${response.status}`;
        try {
          const payload = await response.json();
          if (payload?.error?.message) {
            errMessage = payload.error.message;
          }
        } catch {
          // Fallback to HTTP status description
        }
        throw new Error(errMessage);
      }

      if (!response.body) {
        throw new Error("Empty streaming response body received from server.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let buffer = "";
      let fullText = "";

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;

        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          
          // Save the last incomplete chunk to parser buffer
          buffer = lines.pop() || "";

          for (const line of lines) {
            const cleanLine = line.trim();
            if (!cleanLine) continue;

            if (cleanLine.startsWith("data: ")) {
              const contentValue = cleanLine.substring(6);

              if (contentValue === "[DONE]") {
                done = true;
                break;
              }

              let event: Record<string, unknown> | null = null;
              try {
                event = JSON.parse(contentValue);
              } catch {
                // Not valid JSON — fall through to legacy text parsing below
              }

              if (event !== null) {
                if (event.type === "conversation_id") {
                  options.onConversationCreated?.(event.value as string);
                } else if (event.type === "status") {
                  options.onStatusChange?.(event.value as string, event.query as string | undefined);
                } else if (event.type === "research_plan") {
                  options.onResearchPlan?.(event.value as string[]);
                } else if (event.type === "agent_start") {
                  options.onAgentStart?.(event.agent as string, event.label as string);
                } else if (event.type === "tool_start") {
                  options.onToolStart?.(event.tool as string, event.label as string);
                } else if (event.type === "tool_result") {
                  options.onToolResult?.(event.tool as string, event.success as boolean, event.data, event.label as string, event.error as string | undefined);
                } else if (event.type === "code_result") {
                  options.onCodeResult?.(event.data);
                } else if (event.type === "agent_complete") {
                  options.onAgentComplete?.(event.tool_activity);
                } else if (event.type === "sources") {
                  options.onSources?.(event.value as unknown[]);
                } else if (event.type === "text") {
                  fullText += event.value as string;
                  options.onChunk(fullText);
                } else if (event.type === "error") {
                  // Always throw error events so they reach onError handler
                  throw new Error((event.value as string) || "An unknown error occurred.");
                }
                // message_start / message_complete / done — acknowledged, no action needed
              } else {
                // Legacy plain text tokens
                if (contentValue.startsWith("[CONVERSATION_ID] ")) {
                  const newId = contentValue.substring(18).trim();
                  options.onConversationCreated?.(newId);
                } else if (contentValue.startsWith("[SOURCES] ")) {
                  try {
                    const sourcesJson = contentValue.substring(10).trim();
                    const parsed = JSON.parse(sourcesJson);
                    options.onSources?.(parsed);
                  } catch (err) {
                    console.error("Failed to parse sources token:", err);
                  }
                } else if (contentValue.startsWith("[ERROR]")) {
                  throw new Error(contentValue.substring(7).trim());
                } else {
                  fullText += contentValue;
                  options.onChunk(fullText);
                }
              }
            }
          }
        }
      }

      // Flush remaining buffer data
      if (buffer.trim()) {
        const cleanLine = buffer.trim();
        if (cleanLine.startsWith("data: ")) {
          const contentValue = cleanLine.substring(6);
          if (contentValue !== "[DONE]") {
            try {
              const event = JSON.parse(contentValue);
              if (event.type === "text") {
                fullText += event.value;
                options.onChunk(fullText);
              }
            } catch {
              if (!contentValue.startsWith("[ERROR]") && !contentValue.startsWith("[CONVERSATION_ID]") && !contentValue.startsWith("[SOURCES]")) {
                fullText += contentValue;
                options.onChunk(fullText);
              }
            }
          }
        }
      }

      options.onComplete(fullText);

    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error(String(err));
      if (errorObj.name === "AbortError" || signal.aborted) {
        // Ignore aborted signal events cleanly
        return;
      }
      options.onError(errorObj);
    }
  };

  execute();

  return {
    stop: () => {
      controller.abort();
    },
  };
}
