# Phase 21 System Audit: Intelligence, Security, Performance & UX

## Executive Summary
This document provides a comprehensive system audit of the NOVA AI full-stack codebase following Phase 20 completion. The audit identifies critical security vulnerabilities, performance bottlenecks, error handling gaps, streaming edge cases, RAG failure points, and UI/accessibility limitations.

---

## 1. Security Weaknesses & Vulnerabilities

### 1.1 Document API Wrapper Inconsistencies
- `src/lib/api/documents.ts` uses raw `fetch()` directly instead of `fetchApi()`.
- **Impact**: 401 Unauthorized responses from document management APIs bypass global session expiration notifications, leaving unauthenticated states active on the client.

### 1.2 Multi-Tenant Ownership Verification Gaps
- `backend/app/api/routes/conversations.py` and `documents.py` contain some queries where parameters are checked against `current_user.id`, but list/batch operations or child resources (such as message sources or document status checks) require strict tenant assertion before returning data.

### 1.3 Prompt Injection Boundaries
- In `backend/app/agents/document_agent.py` and `task_agent.py`, retrieved document chunks and tool results are wrapped in delimiter blocks (`=== BEGIN UNTRUSTED RETRIEVED CONTENT ===`), but `research_agent.py` and direct chat routes lack defensive system instructions against document injection attacks.

---

## 2. Performance Bottlenecks & Network Optimization

### 2.1 Unnecessary API Requests & Missing AbortControllers
- Search in `CommandPalette.tsx` invokes `searchConversations()` on input change, but rapid typing initiates multiple overlapping backend queries without cancelling stale requests using an `AbortController`.
- `handleSelectChat` in `src/app/page.tsx` fetches messages sequentially without cancelling pending message loads when switching rapidly between conversations.

### 2.2 Re-render Cascades
- In `src/app/page.tsx`, stream token updates trigger `setChats` state changes that cause re-renders across the full conversation list and main layout.

---

## 3. Streaming Edge Cases & State Cleanups

### 3.1 Unmount & Interruption Cleanups
- Stopping generation via `handleStopGeneration` aborts the `streamChatResponse` controller, but active state updates in `onChunk` and `onStatusChange` can fire if events were buffered in memory before cancellation.
- Unexpected socket drops or provider timeouts leave the assistant message in `status: "sending"` or `status: "streaming"` without persisting an error payload or partial response.

---

## 4. RAG Reliability & Document Ingestion Pipeline

### 4.1 Empty & Unsupported File Handling
- Files with zero extractable text (e.g. empty PDFs or scanned images without OCR) seed a generic fallback chunk, but do not communicate an explicit `empty_content` status to the user.
- Queries with zero semantic relevance matches return empty chunk lists; `DocumentAgent` falls back to general knowledge without indicating to the frontend that zero document chunks met the relevance threshold.

---

## 5. Error Handling & Request Correlation

### 5.1 FastAPI Exception Handler Formatting
- `HTTPException` responses with string details return `{ "detail": "...", "error": { "code": "HTTP_EXCEPTION", "message": "...", "request_id": "..." } }`, but custom routes throwing dictionary exceptions omit the standardized `code` envelope or `request_id`.

---

## 6. Accessibility & Mobile UX

### 6.1 Interactive Semantics & Focus Management
- Dropdown menus in `Header.tsx` and message action popovers in `ChatArea.tsx` lack `aria-expanded`, `role="menu"`, and keyboard navigation support (`Escape` to close, arrow key focus trap).
- Modals like `ConfirmationModal` do not restore focus to the triggering element upon closure.

---

## Audit Priority Matrix

| Category | Priority | Action Item | Target File(s) |
| :--- | :--- | :--- | :--- |
| **Security** | High | Standardize `fetchApi` across all client modules | `src/lib/api/documents.ts` |
| **Error Handling** | High | Unify FastAPI exception responses with `request_id` | `backend/app/main.py` |
| **Streaming** | High | Harden stream error recovery & partial text retention | `src/app/page.tsx`, `src/lib/api/chat.ts` |
| **Performance** | Medium | Implement AbortControllers for search & conversation switching | `src/lib/api/conversations.ts`, `CommandPalette.tsx` |
| **RAG** | Medium | Add clear retrieval status and injection boundaries | `backend/app/agents/document_agent.py`, `retrieval_service.py` |
| **Accessibility** | Medium | Add ARIA roles and keyboard traps to popovers/modals | `Header.tsx`, `ChatArea.tsx`, `CommandPalette.tsx` |
