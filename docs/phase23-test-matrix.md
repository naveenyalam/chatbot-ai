# Phase 23 — Comprehensive End-to-End Test Matrix

| ID | Area | Feature | Test | Expected | Actual | Status | Evidence |
|:---|:---|:---|:---|:---|:---|:---:|:---|
| **SYS-01** | Application Health | TypeScript Compilation | `npx tsc --noEmit` | 0 compilation/type errors | Passed with 0 errors | **PASS** | Terminal Output (exit code 0) |
| **SYS-02** | Application Health | Next.js Build | `npm run build` | Clean production static/SSR output | Compiled successfully in 7.3s | **PASS** | Turbopack build log |
| **SYS-03** | Application Health | Backend Python Syntax | `compileall -x venv backend` | Zero syntax or bytecode errors | 100% files compiled cleanly | **PASS** | Python compileall stdout |
| **SYS-04** | Application Health | Pytest Suite | `pytest backend/app/tests` | All unit/integration tests pass | 121 / 121 tests passed (0 failures) | **PASS** | Pytest summary in 91.1s |
| **SYS-05** | Application Health | FastAPI Health Probes | GET `/health` & `/readiness` | HTTP 200 `{"status": "ok/ready"}` | HTTP 200 OK | **PASS** | REST endpoint response |
| **AUTH-01** | Authentication | User Login | Submit valid credentials | Returns JWT & redirects to `/` | User authenticated & redirected | **PASS** | `/api/auth/login` |
| **AUTH-02** | Authentication | Password Visibility Toggle | Click eye icon in password field | Switches between masked & plaintext | Text toggles smoothly | **PASS** | `showPassword` state |
| **AUTH-03** | Authentication | Form Validation | Submit empty email/password | Disables CTA / shows inline notice | Blocked with clean error banner | **PASS** | Form validation check |
| **AUTH-04** | Authentication | User Registration | Submit new user details | Creates account, returns JWT | User registered successfully | **PASS** | `/api/auth/register` |
| **AUTH-05** | Authentication | Session Expiration | Request `/api/auth/me` without token | HTTP 401 Unauthorized | Clears session and redirects to `/login` | **PASS** | Auth interceptor |
| **UI-01** | Layout | Sidebar Toggle | Click collapse button | Toggles sidebar expanded/collapsed | Smooth spring animation | **PASS** | Framer motion state |
| **UI-02** | Layout | Workspace Selection | Change workspace via header | Switches active view & prompt templates | UI & suggestion cards update | **PASS** | `WorkspaceView` state |
| **UI-03** | Layout | Model Selector | Select `NOVA Intelligence 3.5` | Changes active LLM engine | Request header sends selected model | **PASS** | Header dropdown |
| **UI-04** | Layout | Theme Switcher | Click theme toggle | Toggles light and dark themes | CSS variables & DOM class updated | **PASS** | `ThemeProvider` hook |
| **CHAT-01** | Chat Execution | Message Streaming | Send prompt to AI engine | Streams SSE chunks incrementally | Real-time streaming without token loss | **PASS** | `/api/chat/stream` |
| **CHAT-02** | Chat Execution | Multiline Compose | Shift + Enter in textarea | Inserts newline without submitting | Textarea expands smoothly | **PASS** | `ChatInput` keydown handler |
| **CHAT-03** | Chat Execution | Stop Generation | Click stop button mid-stream | Aborts active SSE stream | Stream cancelled immediately | **PASS** | `AbortController.abort()` |
| **CHAT-04** | Chat Execution | Message Action - Copy | Click copy button on AI response | Copies raw response to clipboard | Toast "Copied to clipboard" | **PASS** | `navigator.clipboard` |
| **CHAT-05** | Chat Execution | Edit Message | Click edit icon on user message | Re-streams response from edit point | Thread updated cleanly | **PASS** | `handleEditMessage` |
| **CHAT-06** | Chat Execution | Export Conversation | Select Export -> Markdown | Downloads `.md` file with title | Valid `.md` file downloaded | **PASS** | `handleExportChat` Blob URL |
| **RAG-01** | Knowledge Base | Document Upload | Drag & drop PDF/TXT document | Uploads and starts vector indexing | Document status shows `Ready` | **PASS** | `/api/documents/upload` |
| **RAG-02** | Knowledge Base | Ask NOVA Trigger | Click "Ask NOVA" on indexed doc | Binds document to chat context bar | Document added to context selection | **PASS** | `DocumentLibrary` click handler |
| **RAG-03** | Knowledge Base | Context Indicator Bar | Inspect top of ChatArea | Displays active doc count & popover | Popover opens with indexed files | **PASS** | `ChatArea` RAG drawer |
| **SRCH-01**| Global Search | Command Palette (Ctrl+K) | Press Ctrl+K & type query | Displays chats, docs, prompts | `unifiedSearch` categorizes results | **PASS** | `CommandPalette` unified search |
| **SETT-01**| Settings | Preferences Update | Change model detail level | Persists preferences across refresh | Preferences saved in backend/local | **PASS** | `/api/preferences` |
| **SEC-01** | Security | Sandbox Execution | Execute system commands in sandbox | Sandbox blocks dangerous imports | Execution halted safely | **PASS** | RestrictedPython engine |
