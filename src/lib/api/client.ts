import { handleNetworkError } from "./error";

// Base API configuration parameters and centralized HTTP client helpers
export const API_URL = process.env.NEXT_PUBLIC_API_URL !== undefined ? process.env.NEXT_PUBLIC_API_URL : "http://localhost:8000";

let isSessionExpiredNotified = false;
const sessionExpiredListeners: Array<() => void> = [];

/**
 * Register a callback to be notified when an HTTP 401 Unauthorized status is returned by any API call.
 */
export function onSessionExpired(callback: () => void): () => void {
  sessionExpiredListeners.push(callback);
  return () => {
    const index = sessionExpiredListeners.indexOf(callback);
    if (index > -1) {
      sessionExpiredListeners.splice(index, 1);
    }
  };
}

/**
 * Reset the session expiration dispatch flag (e.g. after successful login).
 */
export function resetSessionExpiredFlag(): void {
  isSessionExpiredNotified = false;
}

/**
 * Dispatch session expiration event once to all subscribers.
 */
export function notifySessionExpired(): void {
  if (isSessionExpiredNotified) return;
  isSessionExpiredNotified = true;
  sessionExpiredListeners.forEach((cb) => {
    try {
      cb();
    } catch (err) {
      console.error("Error in session expired listener:", err);
    }
  });
}

/**
 * Standardized fetch wrapper that intercepts 401 Unauthorized errors gracefully.
 */
export async function fetchApi(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const url = endpoint.startsWith("http") ? endpoint : `${API_URL}${endpoint}`;
  const config: RequestInit = {
    ...options,
    credentials: options.credentials || "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    if (response.status === 401 && !endpoint.includes("/api/auth/login") && !endpoint.includes("/api/auth/register")) {
      notifySessionExpired();
    }
    return response;
  } catch (error) {
    const normalized = handleNetworkError(error);
    console.warn(`Network fetch failed for ${url}:`, normalized.message);
    throw new Error(normalized.message);
  }
}
