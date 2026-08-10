# Phase 22 Product Architecture & Workspace Specification

## Executive Overview
Phase 22 transforms NOVA AI into a unified AI productivity workspace. The application integrates Chat, Knowledge Base, Research Workspace, Developer Sandbox, Data Analysis, AI Autonomous Agents, and Productivity Tools into a single responsive client-server environment.

---

## 1. Current Architecture & Capability Mapping

### Existing Foundations (Phases 1–21)
- **Authentication**: JWT-in-HttpOnly cookies with session expiration handling and user models (`User`).
- **Conversations & Chat Engine**: SSE streaming (`streamChatResponse`), AI auto-titling, message deletion, prompt context windowing, message sources (`MessageSource`).
- **RAG & Document Intelligence**: Multi-format extraction (PDF, DOCX, TXT, MD, CSV, PNG, JPG, WEBP), magic-byte signature validation, background vector chunking, pgvector / SQLite cosine similarity search (`retrieve_relevant_chunks`).
- **Agent Orchestration**: `AgentManager` and `BaseAgent` loop (`ChatAgent`, `DocumentAgent`, `ResearchAgent`, `TaskAgent`) emitting tool activity and sources.
- **Developer Sandbox**: Restricted Python execution sandbox with AST validation and variable output capture.
- **UI Design System**: Dark/Light mode theme provider (`ThemeProvider`), glassmorphism panels, CSS variables, `Header`, `Sidebar`, `ChatArea`, `CommandPalette`.

### Missing Capabilities to Implement in Phase 22
- **Persistent Workspace Navigation & Mode Switcher**: Workspace switcher across General AI, Research, Coding, Documents, Data Analysis, and Agent modes.
- **Collections & Document Management**: Document collections (`Collection`, `DocumentCollection`) to group files, drag-and-drop ingestion, file status badges, split-view document previewer.
- **Data Analysis Workspace**: Dataset analysis engine for CSV/JSON/XLSX with column metadata, automated statistics, summary insights, and interactive table/chart views.
- **Productivity Engine**:
  - **Prompt Library**: Persistent user prompts (`Prompt`, `PromptCategory`) with template variables (`{{variable}}`) and quick insertion UI.
  - **Chat Templates**: System templates with variable input modal.
  - **Saved Responses**: Bookmarked AI responses (`SavedResponse`) with full-text search and tags.
- **Real-Time Notification System**: User notifications (`Notification`) for processing status, agent runs, research completion, and system errors with unread counters.
- **Unified Global Search & Command Center**: Server-backed multi-resource search across Conversations, Messages, Documents, Collections, Prompts, and Saved Responses.

---

## 2. Technical Risk Analysis & Mitigation

| Technical Area | Potential Risk | Mitigation Strategy |
| :--- | :--- | :--- |
| **Data Isolation** | Cross-tenant data leakage on new endpoints | Enforce mandatory `user_id == current_user.id` SQL filtering on all queries |
| **Workspace State Sync** | Lost user input when switching workspaces | Store active workspace in `localStorage` and app state without unmounting global chat context |
| **Large File / Data Analysis** | Memory overload when parsing large CSVs/JSONs | Process data client-side in web workers or stream metadata summaries from backend |
| **Database Migrations** | Schema conflicts with existing tables | Create clean SQLAlchemy models (`Prompt`, `Collection`, `SavedResponse`, `Notification`, `WorkspacePreference`) with clear foreign keys |

---

## 3. Recommended Implementation Order

1. **Database & Schema Layer**: Implement SQLAlchemy models for Collections, Prompts, Saved Responses, Notifications, and Workspace Preferences.
2. **Backend API Layer**: Add REST endpoints for collections, prompts, saved responses, notifications, workspace preferences, and unified search.
3. **Workspace Navigation & Switcher**: Build collapsible sidebar navigation and header workspace selector.
4. **Knowledge & Document Collections**: Build drag-and-drop collections UI, file status badges, and document preview split-panel.
5. **Research Workspace**: Build multi-phase research progress workspace (Question -> Search -> Sources -> Analysis -> Report).
6. **Coding & Data Analysis Workspaces**: Build file tree code editor view and dataset analyzer view.
7. **Productivity Tools**: Build Prompt Library with variable input modal, Chat Templates, and Saved Responses panel.
8. **Notification & Command Center**: Build real-time Notification Center and upgrade Command Palette into unified search center.
9. **Verification & Testing**: Run pytest backend tests, TypeScript validation (`npx tsc --noEmit`), and production Next.js build (`npm run build`).
