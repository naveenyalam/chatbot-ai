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

      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: payloadMessages,
          model: options.model || "nova-intelligence",
          temperature: options.temperature ?? 0.7,
          conversation_id: options.conversation_id,
          document_ids: options.document_ids,
          mode: options.mode,
          workspace_mode: options.mode,
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

              try {
                const event = JSON.parse(contentValue);
                if (event.type === "conversation_id") {
                  options.onConversationCreated?.(event.value);
                } else if (event.type === "status") {
                  options.onStatusChange?.(event.value, event.query);
                } else if (event.type === "research_plan") {
                  options.onResearchPlan?.(event.value);
                } else if (event.type === "agent_start") {
                  options.onAgentStart?.(event.agent, event.label);
                } else if (event.type === "tool_start") {
                  options.onToolStart?.(event.tool, event.label);
                } else if (event.type === "tool_result") {
                  options.onToolResult?.(event.tool, event.success, event.data, event.label, event.error);
                } else if (event.type === "code_result") {
                  options.onCodeResult?.(event.data);
                } else if (event.type === "agent_complete") {
                  options.onAgentComplete?.(event.tool_activity);
                } else if (event.type === "sources") {
                  options.onSources?.(event.value);
                } else if (event.type === "text") {
                  fullText += event.value;
                  options.onChunk(fullText);
                } else if (event.type === "error") {
                  throw new Error(event.value);
                }
              } catch (e) {
                if (e instanceof Error && e.message !== "Unexpected token" && !e.message.includes("JSON")) {
                  // Re-raise actual downstream errors (like those thrown by error event)
                  throw e;
                }
                // Backward compatible legacy plain text tokens parsing
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
