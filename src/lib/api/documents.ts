import { API_URL, fetchApi, notifySessionExpired } from "./client";
import { parseApiError } from "./error";

export interface DocumentResponse {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  status: "uploaded" | "processing" | "indexed" | "failed" | "deleted";
  page_count: number;
  created_at: string;
}

export interface DocumentStatusResponse {
  id: string;
  status: "uploaded" | "processing" | "indexed" | "failed" | "deleted";
  page_count: number;
}

/**
 * Uploads a document to the server with real-time upload progress.
 */
export function uploadDocument(
  file: File,
  onProgress?: (percent: number) => void
): Promise<DocumentResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_URL}/api/documents/upload`);
    xhr.withCredentials = true;

    // Track upload progress
    if (onProgress && xhr.upload) {
      xhr.upload.onprogress = (evt) => {
        if (evt.lengthComputable) {
          const percent = Math.round((evt.loaded / evt.total) * 100);
          onProgress(percent);
        }
      };
    }

    xhr.onload = async () => {
      if (xhr.status === 401) {
        notifySessionExpired();
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res = JSON.parse(xhr.responseText);
          resolve(res);
        } catch (err) {
          reject(new Error("Failed to parse upload response."));
        }
      } else {
        try {
          const errorBody = JSON.parse(xhr.responseText);
          const msg = errorBody?.error?.message || errorBody?.detail || "Upload failed.";
          reject(new Error(msg));
        } catch {
          reject(new Error(`Upload failed with status code: ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => {
      reject(new Error("Network connection error during file upload."));
    };

    const formData = new FormData();
    formData.append("file", file);
    xhr.send(formData);
  });
}

/**
 * Fetch all documents owned by the authenticated user.
 */
export async function listDocuments(): Promise<DocumentResponse[]> {
  const response = await fetchApi("/api/documents", {
    method: "GET",
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }

  return response.json();
}

/**
 * Fetch status of a specific document (e.g. for polling).
 */
export async function getDocumentStatus(id: string): Promise<DocumentStatusResponse> {
  const response = await fetchApi(`/api/documents/${id}/status`, {
    method: "GET",
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }

  return response.json();
}

/**
 * Delete a document from storage and index.
 */
export async function deleteDocument(id: string): Promise<void> {
  const response = await fetchApi(`/api/documents/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }
}

/**
 * Fetch sources metadata used in a conversation.
 */
export async function listConversationSources(id: string): Promise<DocumentResponse[]> {
  const response = await fetchApi(`/api/conversations/${id}/sources`, {
    method: "GET",
  });

  if (!response.ok) {
    const err = await parseApiError(response);
    throw new Error(err.message);
  }

  return response.json();
}
