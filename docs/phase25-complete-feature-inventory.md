# Phase 25 — Complete Feature Inventory

This document compiles the exhaustive structural and functional components inventory of the NOVA AI codebase, covering frontend routes, backend routes, React views, UI controls, shortcuts, and key codebase patterns.

---

## 1. Application Architecture & Routes

### 1.1 Frontend Routes (Next.js App Router)
* **`/` (Root Page):** `src/app/page.tsx` — Main application dashboard. Manages workspace rendering, chat view, and sidebar integrations.
* **`/login`:** `src/app/login/page.tsx` — User authentication login interface.
* **`/register`:** `src/app/register/page.tsx` — New account registration interface.
* **`/error`:** `src/app/error.tsx` — Global application fallback page for uncaught exceptions.

### 1.2 Backend API Routes (FastAPI)
* **Auth System:**
  * `POST /api/auth/register`
  * `POST /api/auth/login`
  * `POST /api/auth/logout`
  * `GET /api/auth/me`
* **Chat Engine:**
  * `POST /api/chat/stream`
* **Conversation Management:**
  * `GET /api/conversations`
  * `POST /api/conversations`
  * `GET /api/conversations/{id}`
  * `PATCH /api/conversations/{id}`
  * `DELETE /api/conversations/{id}`
  * `POST /api/conversations/{id}/generate-title`
  * `GET /api/conversations/{id}/messages`
  * `DELETE /api/conversations/{id}/messages/{message_id}`
  * `GET /api/conversations/search`
* **Document RAG System:**
  * `POST /api/documents/upload`
  * `GET /api/documents`
  * `GET /api/documents/{id}`
  * `GET /api/documents/{id}/status`
  * `DELETE /api/documents/{id}`
* **Collections Management:**
  * `GET /api/collections`
  * `POST /api/collections`
  * `DELETE /api/collections/{collection_id}`
  * `POST /api/collections/{collection_id}/documents`
* **Settings & Templates:**
  * `GET /api/preferences`
  * `PUT /api/preferences`
  * `GET /api/prompts`
  * `POST /api/prompts`
  * `PATCH /api/prompts/{prompt_id}`
  * `DELETE /api/prompts/{prompt_id}`
  * `GET /api/saved-responses`
  * `POST /api/saved-responses`
  * `DELETE /api/saved-responses/{response_id}`
* **Unified Search:**
  * `GET /api/search`
* **Workspace Engine:**
  * `GET /api/workspaces`
  * `GET /api/workspaces/{workspace_id}`
  * `POST /api/workspaces/{workspace_id}/validate`
  * `POST /api/workspaces/{workspace_id}/chat`
* **Observability & Diagnostics:**
  * `GET /health`
  * `GET /api/health`
  * `GET /api/provider-status`
  * `GET /metrics`
  * `GET /readiness` / `GET /ready`

---

## 2. React Components Inventory

### 2.1 Layout Components (`src/components/layout/`)
* **`MainLayout.tsx`:** Coordinates rendering of Sidebar, Header, and primary content.
* **`Header.tsx`:** Contains user details, notifications bell, theme switch, and responsive mobile nav drawer triggers.
* **`Sidebar.tsx`:** Manages workspace mode switcher buttons, conversation histories lists, and logout actions.

### 2.2 UI Core Controls (`src/components/ui/`)
* **`Button.tsx`:** Polymorphic button supporting glassy/primary/secondary/danger styling variants.
* **`Input.tsx`:** Input controls with accessibility labels and custom border glow.
* **`GlassPanel.tsx`:** Backdrop-filter container for glassmorphism styling effects.
* **`Badge.tsx`:** Small status indicator pill (e.g. `indexed`, `uploaded`, `pending`).
* **`Toast.tsx`:** System-wide feedback message notifications.
* **`ConfirmationModal.tsx`:** Overlay window prompting user before critical actions.
* **`ErrorBoundary.tsx`:** Catch-all React boundary containing error display and retry triggers.
* **`NotificationCenter.tsx`:** Panel rendering user notification alerts.
* **`CommandPalette.tsx`:** Overlay dialog displaying fast options menu on hotkey.

### 2.3 Dashboard Views (`src/components/dashboard/`)
* **`DashboardOverview.tsx`:** Main dashboard landing page containing workspace stats and quick actions.

### 2.4 Chat Components (`src/components/chat/`)
* **`ChatArea.tsx`:** Message stream list, token typing rendering, and action items.
* **`ChatInput.tsx`:** Message input textarea, attachment uploads button, voice trigger, and parameter dials.
* **`ChatWelcome.tsx`:** Intro panel rendering quick prompt suggestions.
* **`CodeBlock.tsx`:** Syntax highlighting renderer for code sections with copy buttons.
* **`MarkdownRenderer.tsx`:** HTML/Markdown stream text parser.
* **`SourcePanel.tsx` & `SourcePreviewPanel.tsx`:** Visual references to document chunks retrieved during RAG queries.

### 2.5 Workspaces View Controls (`src/components/workspaces/`)
* **`ResearchWorkspace.tsx`:** Workspace supporting query workflows, literature scanning, and notes.
* **`CodingWorkspace.tsx`:** Code editor sidebars, execution results, and debug controls.
* **`DataAnalysisWorkspace.tsx`:** Interface for CSV uploads, graphing data tables, and analysis tasks.

### 2.6 Agent Component (`src/components/agents/`)
* **`AgentWorkspace.tsx`:** Interface listing active multi-agent setups, tools, and execution processes.

### 2.7 Settings Panel (`src/components/settings/`)
* **`SettingsPanel.tsx`:** Extensive settings tab controls for system-wide configuration.

---

## 3. UI Controls & Interactive Events

### 3.1 Buttons & Clicks (`onClick`)
* **New Chat Button:** Triggers transition back to initial chat screen (`src/components/layout/Sidebar.tsx`).
* **Clear Conversation History:** Opens Confirmation Modal for database deletion (`src/components/layout/Sidebar.tsx`).
* **SendMessage Button:** Dispatches stream request to `/api/chat/stream` (`src/components/chat/ChatInput.tsx`).
* **Stop Generation:** Aborts current LLM HTTP stream connection via `AbortController` (`src/components/chat/ChatArea.tsx`).
* **Regenerate Response:** Re-dispatches last user prompt to stream completion API (`src/components/chat/ChatArea.tsx`).
* **Copy Response:** Copies text to clipboard with feedback toast (`src/components/chat/ChatArea.tsx`).
* **Edit Message:** Toggle text input mode for a user message (`src/components/chat/ChatArea.tsx`).
* **Confirm Delete Document:** Calls `DELETE /api/documents/{id}` (`src/components/documents/DocumentLibrary.tsx`).
* **Settings Toggle / Close:** Shows or hides sliding SettingsPanel.

### 3.2 Form Submissions (`onSubmit`)
* **Login Form:** Validates credentials and calls `/api/auth/login` (`src/app/login/page.tsx`).
* **Register Form:** Validates parameters and calls `/api/auth/register` (`src/app/register/page.tsx`).
* **Save Preference Form:** Updates db records via `PUT /api/preferences`.

### 3.3 Inputs & Sliders (`onChange`)
* **Textarea Composition:** Auto-resizes height on input change (`src/components/chat/ChatInput.tsx`).
* **Temperature Dial:** Slider adjusting model creativity setting (`src/components/chat/ChatInput.tsx`).
* **Theme Picker:** Switches body attributes between `dark`/`light`/`cyberpunk` classes.

---

## 4. Hotkeys & Global Shortcuts

* **`Ctrl + K` or `Cmd + K`:** Toggles the global Command Palette dialog (`src/components/ui/CommandPalette.tsx`).
* **`Esc`:** Dismisses overlays, command palette, open modals, or active dropdown menus.
* **`Enter`:** Submits messages when "Enter to Send" is checked.
* **`Shift + Enter`:** Inserts carriage return newline inside chat textarea.
* **`Ctrl + Enter`:** Forces message submit when "Ctrl + Enter to Send" is toggled in settings.
* **`Tab` / `Shift + Tab`:** Focus movement cycles logically through form inputs, modals, and header items.

---

## 5. Mock / Local Development References found

* **`dummy-local-key`:** API key configured in `.env` for testing.
* **`http://localhost:8005/v1`:** Local OpenAI mock completions endpoint.
* **`MockLLMProvider`:** Secondary provider fallback class inside `backend/app/services/llm_provider.py` (explicitly bypassed in live mode).
