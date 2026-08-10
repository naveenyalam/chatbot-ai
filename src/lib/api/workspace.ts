import { fetchApi } from "./client";
import { parseApiError } from "./error";

export interface CollectionItem {
  id: string;
  name: string;
  description?: string;
  color?: string;
  document_count: number;
  created_at: string;
}

export interface PromptItem {
  id: string;
  title: string;
  content: string;
  category: string;
  is_favorite: boolean;
  variables: string[];
  created_at: string;
}

export interface SavedResponseItem {
  id: string;
  title: string;
  content: string;
  conversation_id?: string;
  message_id?: string;
  category?: string;
  is_favorite?: boolean;
  created_at: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  category: "document" | "agent" | "research" | "export" | "system";
  is_read: boolean;
  link?: string;
  created_at: string;
}

export interface UserPreferences {
  default_workspace: string;
  default_model: string;
  response_detail: string;
  response_tone: string;
  language: string;
  composer_behavior: string;
}

export interface UnifiedSearchResults {
  conversations: { id: string; title: string; type: "conversation" }[];
  documents: { id: string; name: string; type: "document" }[];
  prompts: { id: string; title: string; type: "prompt" }[];
  saved_responses: { id: string; title: string; type: "saved_response" }[];
}

// --- Collections API ---

export async function listCollections(): Promise<CollectionItem[]> {
  const res = await fetchApi("/api/collections", { method: "GET" });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
  return res.json();
}

export async function createCollection(data: { name: string; description?: string; color?: string }): Promise<CollectionItem> {
  const res = await fetchApi("/api/collections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
  return res.json();
}

export async function deleteCollection(id: string): Promise<void> {
  const res = await fetchApi(`/api/collections/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
}

export async function addDocumentToCollection(collectionId: string, documentId: string): Promise<void> {
  const res = await fetchApi(`/api/collections/${collectionId}/documents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId }),
  });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
}

// --- Prompts API ---

export async function listPrompts(): Promise<PromptItem[]> {
  const res = await fetchApi("/api/prompts", { method: "GET" });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
  return res.json();
}

export async function createPrompt(data: { title: string; content: string; category?: string; variables?: string[] }): Promise<PromptItem> {
  const res = await fetchApi("/api/prompts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
  return res.json();
}

export async function updatePrompt(id: string, data: Partial<PromptItem>): Promise<PromptItem> {
  const res = await fetchApi(`/api/prompts/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
  return res.json();
}

export async function deletePrompt(id: string): Promise<void> {
  const res = await fetchApi(`/api/prompts/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
}

// --- Saved Responses API ---

export async function listSavedResponses(): Promise<SavedResponseItem[]> {
  const res = await fetchApi("/api/saved-responses", { method: "GET" });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
  return res.json();
}

export async function createSavedResponse(data: { title: string; content: string; conversation_id?: string; message_id?: string; category?: string }): Promise<SavedResponseItem> {
  const res = await fetchApi("/api/saved-responses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
  return res.json();
}

export async function deleteSavedResponse(id: string): Promise<void> {
  const res = await fetchApi(`/api/saved-responses/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
}

// --- Notifications API ---

export async function listNotifications(): Promise<{ unread_count: number; notifications: NotificationItem[] }> {
  try {
    const res = await fetchApi("/api/notifications", { method: "GET" });
    if (!res.ok) {
      const err = await parseApiError(res);
      throw new Error(err.message);
    }
    return await res.json();
  } catch {
    return { unread_count: 0, notifications: [] };
  }
}

export async function markNotificationsRead(ids?: string[], markAll: boolean = false): Promise<void> {
  const res = await fetchApi("/api/notifications/mark-read", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids, mark_all: markAll }),
  });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
}

// --- Preferences API ---

export async function getPreferences(): Promise<UserPreferences> {
  try {
    const res = await fetchApi("/api/preferences", { method: "GET" });
    if (!res.ok) {
      const err = await parseApiError(res);
      throw new Error(err.message);
    }
    return await res.json();
  } catch {
    return {
      default_workspace: "chat",
      default_model: "intelligence",
      response_detail: "balanced",
      response_tone: "professional",
      language: "en",
      composer_behavior: "enter_send",
    };
  }
}

export async function updatePreferences(data: Partial<UserPreferences>): Promise<UserPreferences> {
  const res = await fetchApi("/api/preferences", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
  const json = await res.json();
  return json.preferences;
}

// --- Unified Search API ---

export async function unifiedSearch(query: string, signal?: AbortSignal): Promise<UnifiedSearchResults> {
  if (!query || query.trim().length < 2) {
    return { conversations: [], documents: [], prompts: [], saved_responses: [] };
  }
  const res = await fetchApi(`/api/search?q=${encodeURIComponent(query)}`, {
    method: "GET",
    signal,
  });
  if (!res.ok) {
    const err = await parseApiError(res);
    throw new Error(err.message);
  }
  return res.json();
}
