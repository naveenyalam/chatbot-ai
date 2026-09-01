import { handleNetworkError } from "./error";

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL !== undefined && process.env.NEXT_PUBLIC_API_URL !== ""
  ? process.env.NEXT_PUBLIC_API_URL
  : "http://localhost:8000";
export const API_URL = rawApiUrl.endsWith("/") ? rawApiUrl.slice(0, -1) : rawApiUrl;


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

/**
 * Generate an AI image via POST /api/images/generate
 */
export async function generateImage(prompt: string, size: string = "1024x1024") {
  const response = await fetchApi("/api/images/generate", {
    method: "POST",
    body: JSON.stringify({ prompt, size }),
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to generate image.");
  }

  return response.json();
}

/**
 * Trigger secure image download via proxy endpoint or browser blob download.
 */
export async function downloadImage(imageUrl: string, filename: string = "nova_ai_image.png") {
  try {
    const proxyUrl = `${API_URL}/api/images/proxy-download?image_url=${encodeURIComponent(imageUrl)}&filename=${encodeURIComponent(filename)}`;
    const resp = await fetch(proxyUrl, { credentials: "include" });
    if (!resp.ok) throw new Error("Proxy download failed");

    const blob = await resp.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  } catch (err) {
    console.warn("Proxy download failed, falling back to direct window open:", err);
    window.open(imageUrl, "_blank");
  }
}
