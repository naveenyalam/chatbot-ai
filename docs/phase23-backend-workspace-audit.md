# Phase 23 — Backend Workspace Architecture Audit

## 1. Executive Summary
This document provides an audit of the current backend architecture for NOVA AI and outlines the implementation plan for Phase 23: **Complete Modular Backend Workspace Mode Engine**.

---

## 2. Audit of Existing Architecture

### A. Authentication System
- **Module**: `backend/app/api/routes/auth.py` & `backend/app/services/auth_service.py`
- **Mechanism**: JWT Bearer token via HTTP Cookie (`access_token`) or Header (`Authorization: Bearer <token>`).
- **Dependencies**: `get_current_user` injected across API endpoints.

### B. Conversation Management
- **Models**: `backend/app/models/conversation.py` & `backend/app/models/message.py`
- **Routes**: `backend/app/api/routes/conversations.py`
- **Gap Identified**: `Conversation` model needs explicit `workspace_mode` column to persist active mode across sessions.

### C. Chat Streaming & SSE Infrastructure
- **Route**: `POST /api/chat/stream` (`backend/app/api/routes/chat.py`)
- **Protocol**: Server-Sent Events (`text/event-stream`).
- **Event Types**: `conversation_id`, `message_start`, `status`, `text`, `sources`, `tool_start`, `tool_result`, `code_execution`, `error`, `done`.

### D. Model Routing & AI Provider
- **Router**: `backend/app/services/model_router.py`
- **Provider**: `backend/app/services/llm_provider.py` (`OpenAICompatibleProvider`, `NotConfiguredProvider`, `MockLLMProvider`).
- **Error Standard**: Emits `AI_PROVIDER_NOT_CONFIGURED` if `AI_API_KEY` is missing in production.

### E. Agent Manager & RAG Infrastructure
- **Agent Orchestrator**: `backend/app/agents/manager.py` (`AgentManager`)
- **Agents**: `ChatAgent`, `ResearchAgent`, `DocumentAgent`, `TaskAgent`.
- **Tool Policies**: `backend/app/agents/policies.py` (`AGENT_TOOL_POLICIES`).
- **RAG & Search**: `backend/app/services/document/` & `backend/app/services/search/`.

---

## 3. Phase 23 Implementation Plan

```mermaid
flowchart TD
    FE["Frontend Workspace Switcher"] -->|GET /api/workspaces| Reg["WorkspaceRegistry"]
    FE -->|POST /api/workspaces/{mode}/chat| Router["Workspace Router"]
    
    Router -->|Lookup| Reg
    Reg -->|Instantiate| WS["BaseWorkspace Instance"]
    
    WS -->|General| GW["GeneralWorkspace"]
    WS -->|Research| RW["ResearchWorkspace"]
    WS -->|Writing| WW["WritingWorkspace"]
    WS -->|Coding| CW["CodingWorkspace (Sandbox Execution)"]
    WS -->|Documents| DW["DocumentWorkspace (RAG Pipeline)"]
    WS -->|Data Analysis| DAW["DataAnalysisWorkspace (Pure Statistical Profiling)"]
    WS -->|Agent| AW["AgentWorkspace (Multi-step Planner)"]
    
    GW --> SSE["Unified SSE Generator"]
    RW --> SSE
    WW --> SSE
    CW --> SSE
    DW --> SSE
    DAW --> SSE
    AW --> SSE
```

### Module Structure (`backend/app/workspaces/`)
- `enums.py`: `WorkspaceMode` Enum (`GENERAL`, `RESEARCH`, `WRITING`, `CODING`, `DOCUMENTS`, `DATA_ANALYSIS`, `AGENT`).
- `schemas.py`: Pydantic request/response schemas for workspace metadata and chat requests.
- `base.py`: Abstract `BaseWorkspace` defining capabilities, system prompts, execution, and validation hooks.
- `general.py`, `research.py`, `writing.py`, `coding.py`, `documents.py`, `data_analysis.py`, `agent.py`: Specialized workspace implementations.
- `registry.py`: `WorkspaceRegistry` singleton for workspace lookup, listing, and validation.
- `router.py`: FastAPI Router for `/api/workspaces` and `/api/workspaces/{workspace_id}/chat`.

---

## 4. Next Implementation Steps
1. Create `backend/app/workspaces/` package and all 7 workspace classes.
2. Update `Conversation` model to persist `workspace_mode`.
3. Expose `/api/workspaces`, `/api/workspaces/{workspace_id}`, and `/api/workspaces/{workspace_id}/chat`.
4. Connect frontend API client (`src/lib/api/chat.ts` & workspace switcher).
5. Comprehensive unit, integration, and E2E test verification.
