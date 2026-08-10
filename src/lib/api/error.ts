/**
 * Centralized API Error handling utility for NOVA AI Frontend.
 * Converts HTTP status codes, API error payloads, and network failures into
 * sanitized, user-friendly messages without exposing internal stack traces or paths.
 */

export interface NormalizedError {
  code: string;
  message: string;
  requestId?: string;
  status?: number;
  isNetworkError?: boolean;
}

export async function parseApiError(response: Response): Promise<NormalizedError> {
  const status = response.status;
  let serverCode = "HTTP_ERROR";
  let serverMessage = "";
  let requestId = response.headers.get("X-Request-ID") || undefined;

  try {
    const data = await response.json();
    if (data?.error) {
      serverCode = data.error.code || serverCode;
      serverMessage = data.error.message || "";
      requestId = data.error.request_id || requestId;
    } else if (data?.detail) {
      serverMessage = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    }
  } catch {
    // Ignore JSON parsing failure
  }

  // Map HTTP status codes to clean user-facing error messages
  let userMessage = serverMessage;

  if (!userMessage) {
    switch (status) {
      case 400:
        userMessage = "Invalid request parameter. Please check your input.";
        serverCode = "BAD_REQUEST";
        break;
      case 401:
        userMessage = "Your session has expired. Please sign in again.";
        serverCode = "UNAUTHORIZED";
        break;
      case 403:
        userMessage = "You do not have permission to perform this action.";
        serverCode = "FORBIDDEN";
        break;
      case 404:
        userMessage = "The requested resource could not be found.";
        serverCode = "NOT_FOUND";
        break;
      case 409:
        userMessage = "A conflict occurred with the current state of the resource.";
        serverCode = "CONFLICT";
        break;
      case 422:
        userMessage = "Unable to process input data. Please verify fields and try again.";
        serverCode = "UNPROCESSABLE_ENTITY";
        break;
      case 429:
        userMessage = "Rate limit exceeded. Please wait a moment before trying again.";
        serverCode = "RATE_LIMIT_EXCEEDED";
        break;
      case 500:
        userMessage = "NOVA encountered an internal server error. Please try again later.";
        serverCode = "INTERNAL_SERVER_ERROR";
        break;
      case 502:
      case 503:
      case 504:
        userMessage = "NOVA service is temporarily unavailable. Please try again in a few moments.";
        serverCode = "SERVICE_UNAVAILABLE";
        break;
      default:
        userMessage = `An unexpected server error occurred (Status ${status}).`;
        break;
    }
  }

  return {
    code: serverCode,
    message: sanitizeErrorMessage(userMessage),
    requestId,
    status,
  };
}

export function handleNetworkError(error: unknown): NormalizedError {
  const errStr = String(error);
  const isNetwork =
    errStr.includes("Failed to fetch") ||
    errStr.includes("NetworkError") ||
    errStr.includes("Failed to connect") ||
    errStr.includes("Network request failed");

  return {
    code: isNetwork ? "NETWORK_ERROR" : "CLIENT_ERROR",
    message: isNetwork
      ? "Unable to connect to NOVA. Please check your internet connection or server status."
      : sanitizeErrorMessage(errStr),
    isNetworkError: isNetwork,
  };
}

/**
 * Strips internal paths, stack traces, and database connection strings from error messages.
 */
function sanitizeErrorMessage(msg: string): string {
  if (!msg) return "An unexpected error occurred.";
  // Strip file paths (C:\... or /home/...)
  let clean = msg.replace(/([A-Z]:\\[^\s]+|\/[^\s]+\.py)/gi, "[file]");
  // Strip internal tracebacks
  if (clean.includes("Traceback (most recent call last)")) {
    clean = "Internal system execution error.";
  }
  // Strip database URLs or secrets
  clean = clean.replace(/postgres(ql)?:\/\/[^\s]+/gi, "[redacted-db-url]");
  clean = clean.replace(/redis:\/\/[^\s]+/gi, "[redacted-redis-url]");
  return clean;
}
