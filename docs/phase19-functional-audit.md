# Phase 19 — Comprehensive Functionality, Performance & Security Audit

## Executive Summary
This audit documents all functional issues, edge cases, state management bugs, security vulnerabilities, and performance bottlenecks identified in the NOVA AI full-stack application prior to the Phase 19 overhaul.

---

## 1. Identified Issues & Severity Matrix

| ID | Domain | Description | Root Cause / File Location | Severity |
|:---|:---|:---|:---|:---|
| **AUD-01** | **RAG Retrieval** | RAG retrieval fails with `AttributeError` when querying PostgreSQL or SQLite vector DB | `backend/app/services/retrieval_service.py` references non-existent property `settings.RAG_RELEVANCE_THRESHOLD` instead of `settings.RAG_MIN_RELEVANCE_SCORE` | **CRITICAL** |
| **AUD-02** | **Frontend Runtime** | `handleSendMessage` throws `ReferenceError: Cannot access 'combinedAttachments' before initialization` | `combinedAttachments` declared via `const` after `handleSendMessage` in `src/app/page.tsx` | **HIGH** |
| **AUD-03** | **AI Streaming** | Stream chunks freeze or fail to update UI when a new conversation is created mid-stream | In `src/app/page.tsx`, `onConversationCreated` converts temporary ID `temp-xxx` to real UUID `real-yyy`. Subsequent `onChunk` handlers close over stale `targetChatId` and fail `c.id === targetChatId` checks | **HIGH** |
| **AUD-04** | **UX / Integrity** | Rapid double-clicks or pressing Enter during generation fires duplicate requests | `handleSendMessage` in `src/app/page.tsx` lacked an `isLoading` guard | **MEDIUM** |
| **AUD-05** | **Chat Switching** | Switching conversations during an active generation marks the newly selected chat as stopped | `handleStopGeneration` referenced updated `activeChatId` state rather than the ID of the chat executing the stream | **MEDIUM** |
| **AUD-06** | **Network / Auth** | Multiple simultaneous 401 unauthenticated requests trigger duplicate session expiration toasts and loops | Missing centralized API error handler and dispatch lock in `src/lib/api/client.ts` | **HIGH** |
| **AUD-07** | **Recovery** | Selecting a deleted or missing conversation on the server leaves the UI in a frozen state | `handleSelectChat` in `src/app/page.tsx` failed to catch 404 response from `listMessages` | **MEDIUM** |
| **AUD-08** | **Regeneration** | Regenerating assistant responses loses associated file attachments and document context | `handleRegenerateMessage` in `src/app/page.tsx` did not extract `attachments` or document IDs from `precedingUserMsg` | **MEDIUM** |
| **AUD-09** | **RAG Ingestion** | Selected document IDs reset to empty before streaming options capture them | In `src/app/page.tsx`, `setSelectedDocIds([])` was called synchronously before `executeResponseStream` evaluated state closure | **HIGH** |
| **AUD-10** | **Settings** | "Send with Enter" and "Context Window" toggles in SettingsPanel were uncontrolled | `SettingsPanel.tsx` had unpersisted `defaultChecked` HTML controls without `ThemeProvider` state backing | **LOW** |

---

## 2. Category Audits

### A. Authentication & Session Reliability
- **Status**: Secure HttpOnly cookies are used.
- **Finding**: On token expiration, multiple API components attempted parallel `getMe` / `listConversations` calls, emitting duplicate toasts.
- **Fix Plan**: Centralize 401 interceptor in `client.ts` with event-driven single-dispatch notification.

### B. Conversation System & Lifecycle
- **Status**: Creation, listing, and deletion endpoints function properly in FastAPI.
- **Finding**: Temporary client-side IDs (`temp-xxx`) assigned on new chat creation disconnect state updates when server returns persistent UUIDs.
- **Fix Plan**: Use a mutable ref (`targetChatIdRef`) in `page.tsx` to maintain dynamic binding during stream lifecycle.

### C. Streaming Architecture & Resiliency
- **Status**: FastAPI `StreamingResponse` yields SSE format with JSON payloads.
- **Finding**: Client disconnection handles SSE termination, but frontend abort signal handling required explicit cleanup to avoid orphan references.

### D. RAG & Document Search
- **Status**: Ingestion, text chunking, and embedding generation function as designed.
- **Finding**: Missing attribute reference in `retrieval_service.py` (`RAG_RELEVANCE_THRESHOLD` vs `RAG_MIN_RELEVANCE_SCORE`) broke vector search.
- **Fix Plan**: Correct property name and add alias in `Settings` class.

### E. Model Routing & Persistence
- **Status**: Model selection dropdown stores selection in `localStorage`.
- **Finding**: `ai_service.py` expected exact model names (`"nova-intelligence"`), ignoring `"intelligence"` or `"fast"` keys sent by UI.
- **Fix Plan**: Add alias resolution map in `ai_service.py` and `model_router.py`.

---

## 3. Implementation Plan
1. Fix backend RAG retrieval in `retrieval_service.py` and `config.py`.
2. Fix frontend scope ordering in `src/app/page.tsx`.
3. Harden streaming lifecycle and active ID tracking using mutable refs in `src/app/page.tsx`.
4. Add double-submission guard `if (isLoading) return;` in `handleSendMessage`.
5. Update `handleStopGeneration` to accept explicit conversation IDs.
6. Connect `sendWithEnter` setting in `Settings` and `ThemeProvider`.
7. Add 401 single-event dispatch interceptor in `src/lib/api/client.ts`.
8. Verify via TypeScript, Next.js build, compileall, and pytest test suite.
