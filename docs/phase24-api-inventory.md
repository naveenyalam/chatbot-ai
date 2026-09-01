# Phase 24 — FastAPI Endpoint Inventory

This document lists all discovered routes in the NOVA AI FastAPI backend, documenting the path, HTTP method, authentication status, database/Redis/AI dependencies, and request/response specifications.

---

## 1. System Health & Observability Endpoints

### 1.1 `GET /health`
* **Purpose:** High-level status health check of backend services.
* **Auth Required:** No
* **Database Dependency:** Yes (Checks SQLite connection)
* **Redis Dependency:** Yes (Checks Redis connection via ping)
* **AI Dependency:** No (Only returns configuration status flags)
* **Response Status:** `200 OK`
* **Response Body:**
  ```json
  {
    "status": "ok",
    "service": "nova-ai-backend",
    "ai_provider": {
      "configured": true,
      "mode": "real",
      "model": "gpt-4o-mini",
      "base_url": "http://localhost:8005/v1"
    },
    "services": {
      "redis": "connected",
      "database": "connected"
    }
  }
  ```

### 1.2 `GET /api/health`
* **Purpose:** Secondary health check endpoint for proxy and gateway health checks.
* **Auth Required:** No
* **Database Dependency:** Yes
* **Redis Dependency:** Yes
* **AI Dependency:** No
* **Response Status:** `200 OK`

### 1.3 `GET /readiness` / `/ready`
* **Purpose:** Kubernetes-compatible readiness probe returning HTTP `200` if Redis & SQLite are active, or HTTP `503` if degraded.
* **Auth Required:** No
* **Database/Redis Dependency:** Yes
* **AI Dependency:** No
* **Response Status:** `200 OK` / `503 Service Unavailable`

### 1.4 `GET /metrics`
* **Purpose:** Exposes raw Prometheus metrics for latency, cache hits, failures, and requests.
* **Auth Required:** No
* **Database/Redis Dependency:** No
* **AI Dependency:** No
* **Response Status:** `200 OK`

### 1.5 `GET /api/provider-status`
* **Purpose:** Safely checks AI provider setup status without exposing keys.
* **Auth Required:** No
* **Database/Redis Dependency:** No
* **AI Dependency:** No
* **Response Status:** `200 OK`

---

## 2. Authentication Lifecycle Endpoints

### 2.1 `POST /api/auth/register`
* **Purpose:** Creates a new user account.
* **Auth Required:** No
* **Database Dependency:** Yes (Creates User record)
* **Redis Dependency:** No
* **AI Dependency:** No
* **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "strongpassword123",
    "name": "Jane Doe"
  }
  ```
* **Response Status:** `201 Created`

### 2.2 `POST /api/auth/login`
* **Purpose:** Authenticates user credentials, sets access JWT token in secure HTTP-only cookie, and returns profile.
* **Auth Required:** No
* **Database Dependency:** Yes
* **Redis Dependency:** No
* **AI Dependency:** No
* **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "strongpassword123"
  }
  ```
* **Response Status:** `200 OK` / `401 Unauthorized` (invalid password)

### 2.3 `POST /api/auth/logout`
* **Purpose:** Clears the client JWT access token cookie.
* **Auth Required:** No
* **Database/Redis Dependency:** No
* **AI Dependency:** No
* **Response Status:** `200 OK`

### 2.4 `GET /api/auth/me`
* **Purpose:** Retrieves the current authenticated user's profile details.
* **Auth Required:** Yes (JWT Bearer Token or Cookie)
* **Database Dependency:** Yes
* **Redis Dependency:** No
* **AI Dependency:** No
* **Response Status:** `200 OK` / `401 Unauthorized`

---

## 3. Chat & Conversation Management Endpoints

### 3.1 `POST /api/chat/stream`
* **Purpose:** Sends user messages to LLM and streams chunked Markdown answers.
* **Auth Required:** Yes
* **Database Dependency:** Yes (Saves conversation messages)
* **Redis Dependency:** Yes (Enforces chat rate limits, checks circuit-breaker status)
* **AI Dependency:** Yes (Streams completions from OpenAICompatibleProvider)
* **Request Body:**
  ```json
  {
    "message": "Write a Python function to calculate factorial.",
    "conversation_id": "optional-uuid",
    "model": "nova-intelligence",
    "temperature": 0.7
  }
  ```
* **Response Status:** `200 OK` (Content-Type: `text/event-stream`)

### 3.2 `GET /api/conversations`
* **Purpose:** List conversations owned by the authenticated user.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Redis/AI Dependency:** No
* **Response Status:** `200 OK`

### 3.3 `POST /api/conversations`
* **Purpose:** Creates a new chat conversation session.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `201 Created`

### 3.4 `GET /api/conversations/{id}`
* **Purpose:** Retrieves a single conversation's details.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK` / `404 Not Found` (non-existent or not owned by caller)

### 3.5 `PATCH /api/conversations/{id}`
* **Purpose:** Updates attributes of a conversation (e.g. title).
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Request Body:** `{"title": "Updated Title"}`
* **Response Status:** `200 OK`

### 3.6 `DELETE /api/conversations/{id}`
* **Purpose:** Deletes conversation and all its messages.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

### 3.7 `POST /api/conversations/{id}/generate-title`
* **Purpose:** Asynchronously generates a summary title using LLM based on conversation messages.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Redis Dependency:** No
* **AI Dependency:** Yes
* **Response Status:** `200 OK`

### 3.8 `GET /api/conversations/{id}/messages`
* **Purpose:** Lists all messages in a conversation.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

### 3.9 `DELETE /api/conversations/{id}/messages/{message_id}`
* **Purpose:** Deletes a specific message.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

### 3.10 `GET /api/conversations/search`
* **Purpose:** Performs full-text queries over conversation history.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

---

## 4. Document Management & RAG Endpoints

### 4.1 `POST /api/documents/upload`
* **Purpose:** Uploads text or PDF document. Initiates background parsing, chunking, and embedding.
* **Auth Required:** Yes
* **Database Dependency:** Yes (Saves Document record)
* **Redis Dependency:** Yes (Enqueues job to background queue via Redis lists)
* **Request Format:** Multipart Form Data (`file`)
* **Response Status:** `202 Accepted`

### 4.2 `GET /api/documents`
* **Purpose:** Lists all documents uploaded by user.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

### 4.3 `GET /api/documents/{id}`
* **Purpose:** Gets metadata of a specific document.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

### 4.4 `GET /api/documents/{id}/status`
* **Purpose:** Checks the parsing/indexing status of an uploaded document (`pending`, `processing`, `completed`, `failed`).
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

### 4.5 `DELETE /api/documents/{id}`
* **Purpose:** Deletes a document and its parsed text chunks from database.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

### 4.6 `GET /api/collections` / `POST /api/collections`
* **Purpose:** Lists or creates collections grouping documents.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK` / `201 Created`

### 4.7 `POST /api/collections/{collection_id}/documents`
* **Purpose:** Links a document to a collection.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

### 4.8 `DELETE /api/collections/{collection_id}`
* **Purpose:** Deletes a collection reference.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

---

## 5. Settings, Preferences & Templates

### 5.1 `GET /api/preferences` / `PUT /api/preferences`
* **Purpose:** Reads or updates user preferences (UI theme, model type, chunk sizes, system prompts).
* **Auth Required:** Yes
* **Database Dependency:** Yes (Settings/Preferences table)
* **Response Status:** `200 OK`

### 5.2 `GET /api/prompts` / `POST /api/prompts`
* **Purpose:** Lists or creates custom prompt library templates.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK` / `201 Created`

### 5.3 `PATCH /api/prompts/{prompt_id}` / `DELETE /api/prompts/{prompt_id}`
* **Purpose:** Updates or deletes prompt templates.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

### 5.4 `GET /api/saved-responses` / `POST /api/saved-responses`
* **Purpose:** Lists or creates saved chat completions.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK` / `201 Created`

### 5.5 `DELETE /api/saved-responses/{response_id}`
* **Purpose:** Removes saved chat response record.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

### 5.6 `GET /api/search`
* **Purpose:** Unified full-text search across messages, templates, and documents.
* **Auth Required:** Yes
* **Database Dependency:** Yes
* **Response Status:** `200 OK`

---

## 6. Workspace Modes Endpoints

### 6.1 `GET /api/workspaces`
* **Purpose:** Lists all configured workspace modes (`generic`, `documents` (RAG), `research`, `coding`, `internet`).
* **Auth Required:** Yes
* **Database/Redis Dependency:** No
* **Response Status:** `200 OK`

### 6.2 `GET /api/workspaces/{workspace_id}`
* **Purpose:** Gets detail definition and limits of a specific workspace mode.
* **Auth Required:** Yes
* **Database/Redis Dependency:** No
* **Response Status:** `200 OK`

### 6.3 `POST /api/workspaces/{workspace_id}/validate`
* **Purpose:** Validates specific workspace configurations before launching a query.
* **Auth Required:** Yes
* **Database/Redis Dependency:** No
* **Response Status:** `200 OK`

### 6.4 `POST /api/workspaces/{workspace_id}/chat`
* **Purpose:** Core chat endpoint for workspace queries. Integrates RAG retrieval, research, coding, or search pipelines depending on mode.
* **Auth Required:** Yes
* **Database Dependency:** Yes (Saves conversation, queries document embeddings/chunks)
* **Redis Dependency:** Yes (Caches embedding vectors, checks rate-limits)
* **AI Dependency:** Yes (Streams responses scoped to workspace context)
* **Response Status:** `200 OK` (Event Stream)
