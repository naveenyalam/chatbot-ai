import { fetchApi } from "./client";
import { parseApiError } from "./error";
import { Message } from "@/types";

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  model: string;
  created_at: string;
  updated_at: string;
}

/**
 * Fetch all conversations for the authenticated user.
 */
export async function listConversations(signal?: AbortSignal): Promise<Conversation[]> {
  const response = await fetchApi("/api/conversations", {
    method: "GET",
    signal,
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }

  return response.json();
}

/**
 * Search conversations by query.
 */
export async function searchConversations(query: string, signal?: AbortSignal): Promise<Conversation[]> {
  if (!query || query.trim().length < 2) return [];
  const response = await fetchApi(`/api/conversations/search?q=${encodeURIComponent(query)}`, {
    method: "GET",
    signal,
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }

  return response.json();
}

/**
 * Create a new conversation instance.
 */
export async function createConversation(title?: string, model?: string): Promise<Conversation> {
  const response = await fetchApi("/api/conversations", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title, model }),
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }

  return response.json();
}

/**
 * Trigger AI auto-generation of conversation title.
 */
export async function generateConversationTitle(id: string): Promise<Conversation> {
  const response = await fetchApi(`/api/conversations/${id}/generate-title`, {
    method: "POST",
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }

  return response.json();
}

/**
 * Rename a conversation.
 */
export async function renameConversation(id: string, title: string): Promise<Conversation> {
  const response = await fetchApi(`/api/conversations/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }

  return response.json();
}

/**
 * Delete a conversation.
 */
export async function deleteConversation(id: string): Promise<void> {
  const response = await fetchApi(`/api/conversations/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }
}

/**
 * Delete a message from a conversation.
 */
export async function deleteMessage(conversationId: string, messageId: string): Promise<void> {
  const response = await fetchApi(`/api/conversations/${conversationId}/messages/${messageId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }
}

/**
 * Fetch messages for a specific conversation.
 */
export async function listMessages(conversationId: string, signal?: AbortSignal): Promise<Message[]> {
  const response = await fetchApi(`/api/conversations/${conversationId}/messages`, {
    method: "GET",
    signal,
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }

  return response.json();
}
