# Phase 25 — API Functional Report

This report documents the functional auditing and safety verification of all major backend endpoints in the NOVA AI FastAPI codebase.

---

## 1. API Route Directory & Specification

| Method | Endpoint | Auth | Request Body / Query Params | Database | Redis | Expected Status |
|--------|----------|------|-----------------------------|----------|-------|-----------------|
| `GET` | `/health` | No | None | No | Yes | `200 OK` |
| `GET` | `/api/health` | No | None | No | Yes | `200 OK` |
| `GET` | `/api/provider-status` | No | None | No | No | `200 OK` |
| `GET` | `/readiness` | No | None | No | Yes | `200 OK` |
| `POST` | `/api/auth/register` | No | `UserCreate` (email, password, name) | Yes | Yes (limiter) | `201 Created` |
| `POST` | `/api/auth/login` | No | `UserLogin` (email, password) | Yes | Yes (limiter) | `200 OK` |
| `POST` | `/api/auth/logout` | Yes | None (Cookie-based session) | No | Yes (session clear) | `200 OK` |
| `GET` | `/api/auth/me` | Yes | None | Yes | No | `200 OK` |
| `GET` | `/api/conversations` | Yes | None | Yes | Yes (cache) | `200 OK` |
| `POST` | `/api/conversations` | Yes | `ConversationCreate` (title) | Yes | Yes (cache delete) | `201 Created` |
| `GET` | `/api/conversations/{id}`| Yes | Path parameter `id` | Yes | No | `200 OK` |
| `DELETE`| `/api/conversations/{id}`| Yes | Path parameter `id` | Yes | Yes (cache delete) | `200 OK` |
| `POST` | `/api/chat/stream` | Yes | `ChatRequest` (messages list, model, temp) | Yes | Yes (RAG context) | `200 OK (Stream)`|
| `POST` | `/api/documents/upload` | Yes | `UploadFile = File(...)` | Yes | Yes (queue/limit) | `201 Created` |
| `GET` | `/api/documents/{id}/status`| Yes| Path parameter `id` | Yes | No | `200 OK` |
| `GET` | `/api/preferences` | Yes | None | Yes | No | `200 OK` |
| `PUT` | `/api/preferences` | Yes | `PreferenceUpdate` (workspace preferences) | Yes | No | `200 OK` |
| `GET` | `/api/workspaces` | Yes | None | No | No | `200 OK` |

---

## 2. Validation & Security Boundaries Test Log

During the test harness run, the following validation and rate limit states were verified:

### 2.1 Diagnostic & Health Checks
* **`/health` & `/api/health`:** Responded with `200 OK` and `"status": "ok"`, confirming successful ping to the Redis cluster.
* **`/readiness`:** Returned `200 OK` confirming system readiness.
* **`/api/provider-status`:** Confirmed that the mock OpenAI server config state was loaded successfully without exposing credentials.

### 2.2 Registration & Login Validation
* **Correct Credentials Login:** User A login returned `200 OK` with session cookie attributes.
* **Invalid Credentials Login:** Returned `401 Unauthorized` (*standardized for production security*).
* **Missing/Invalid Registration Payload:** Returned `400 Bad Request` or `422 Unprocessable Entity` validation errors.
* **Anonymous Profile Check (`/me`):** Returned `401 Unauthorized` blocking access.

### 2.3 Rate Limiter Verification
* **Burst Limit Trigger:** Registering and logging in multiple users in quick succession triggered the backend sliding window rate limiter, returning `429 Too Many Requests`. This confirms rate limits are actively enforced under heavy request bursts to prevent credential stuffing or brute-forcing.

### 2.4 User Workspace Preferences Validation
* **Valid Updates:** Sending `{"default_workspace": "general", "composer_behavior": "ctrl_enter"}` updated user preferences, returning `200 OK`.
* **Invalid Updates:** Sending `{"default_workspace": "invalid_mode_name"}` was caught by our newly added validator and returned `400 Bad Request`, preventing database corruption.

### 2.5 Data Isolation & Privacy Boundary
* **Cross-User Resource Leak Check:** Requesting User A's private conversation from User B's authenticated client context returned `404 Not Found`.
* **Cross-User Document Leak Check:** Accessing User A's uploaded document metadata from User B's context returned `404 Not Found` (or `401 Unauthorized` during limit blocks).
* **Cross-User Directory Check:** Uploads are written to disk nested under `user_<id>/` sub-folders, guaranteeing filesystem-level isolation.
