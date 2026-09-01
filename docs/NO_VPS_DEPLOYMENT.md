# NOVA AI — No-VPS Production Architecture Audit & Plan

## 1. Executive Summary

This document details the transition plan and system specifications to move **NOVA AI** from a local/Docker VPS deployment to a 100% serverless / cloud-managed production stack without relying on any self-hosted virtual private server (VPS) or keeping a local PC online.

---

## 2. Target Production Architecture (VPS-Free)

```
User (Browser)
  ↓
https://YOUR_DOMAIN.com (Vercel Frontend)
  ↓
Next.js 16 (App Router + React 19)
  ↓
FastAPI on Render (Asynchronous Python REST + SSE Streaming API)
  ├── Managed PostgreSQL (Neon / Supabase / Render Postgres)
  ├── Upstash Redis (Serverless / Managed Redis Cache & Rate Limiter)
  └── Cloud LLM Provider API (OpenAI, OpenRouter, Groq, Together, etc.)
```

### Local Development Flow (Unchanged)
```
User (Browser)
  ↓
http://localhost:3000 (Next.js Dev Server)
  ↓
http://localhost:8000 (FastAPI Local Backend)
  ├── SQLite (nova_ai.db) / Local Postgres
  ├── In-Memory Fallback Cache / Local Redis
  └── Ollama (http://127.0.0.1:11434/v1) with qwen2.5:3b model
```

---

## 3. Existing Project Inspection Summary

### Key Configuration Files & Dependencies
* **Frontend**: Next.js 16.3.0, React 19.2.8, Tailwind CSS v4, Framer Motion.
* **Backend**: FastAPI 1.0.0+, SQLAlchemy 2.0, Alembic, Pydantic v2, redis-py, httpx.
* **API Routing**: `NEXT_PUBLIC_API_URL` environment variable controls frontend base URL.
* **Authentication**: JWT token in HTTP-only cookies (`nova_session`) with `SECURE_COOKIES` toggle.
* **Streaming**: Real-time SSE streaming via `streamChatResponse` in `src/lib/api/chat.ts` and `/api/workspaces/{mode}/chat` route in FastAPI backend.

---

## 4. Environment Variables Matrix

### Local Development (.env / .env.local)
| Variable | Value | Description |
| --- | --- | --- |
| `ENV_MODE` | `development` | Enables dev logging and local fallbacks |
| `FRONTEND_URL` | `http://localhost:3000` | Local CORS origin |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend API client target |
| `DATABASE_URL` | `sqlite:///./nova_ai.db` | Local SQLite database |
| `REDIS_URL` | *(optional)* | In-memory fallback if empty |
| `LLM_PROVIDER` | `ollama` | Explicit provider identifier |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434/v1` | Local Ollama endpoint |
| `AI_BASE_URL` | `http://127.0.0.1:11434/v1` | Base URL for LLM requests |
| `AI_MODEL` | `qwen2.5:3b` | Local Ollama model |
| `AI_API_KEY` | `ollama` | Non-empty placeholder for Ollama |
| `JWT_SECRET` | `nova-dev-secret-key-...` | Local JWT signing secret |

### Production (.env on Render & Vercel)
| Variable | Host | Description |
| --- | --- | --- |
| `ENV_MODE` | Render | `production` (enforces strict validation) |
| `FRONTEND_URL` | Render | `https://YOUR_DOMAIN.com` |
| `NEXT_PUBLIC_API_URL` | Vercel | `https://YOUR_RENDER_BACKEND.onrender.com` |
| `DATABASE_URL` | Render | Managed PostgreSQL string (`postgresql://...`) |
| `REDIS_URL` | Render | Upstash Redis connection string (`rediss://...` or `redis://...`) |
| `LLM_PROVIDER` | Render | `openai` / `openrouter` / `groq` / `together` |
| `AI_BASE_URL` | Render | Provider endpoint (e.g., `https://api.openai.com/v1` or `https://openrouter.ai/api/v1`) |
| `AI_MODEL` | Render | Cloud model identifier (e.g. `gpt-4o-mini`, `qwen/qwen-2.5-72b-instruct`) |
| `CLOUD_LLM_API_KEY` / `AI_API_KEY` | Render | Cloud provider API key secret |
| `IMAGE_GENERATION_ENABLED` | Render | `true` (global image AI toggle) |
| `IMAGE_PROVIDER` | Render | `pollinations` / `openai` |
| `IMAGE_MODEL` | Render | `flux` / `dall-e-3` |
| `IMAGE_SIZE` | Render | `1024x1024` |
| `IMAGE_GENERATION_RATE_LIMIT` | Render | `10` (max requests per minute) |
| `IMAGE_GENERATION_MAX_PROMPT_LENGTH` | Render | `1000` (max prompt length) |
| `JWT_SECRET` | Render | Secure 32+ character random string |
| `SECURE_COOKIES` | Render | `true` |

---

## 5. Security & Isolation Rules

1. **No Frontend Secret Leaks**: No API keys, database passwords, or `JWT_SECRET` values will be exposed in `NEXT_PUBLIC_*` environment variables.
2. **Environment-Driven CORS**: CORS configuration reads `FRONTEND_URL` and rejects wildcard `*` when credentials are included in production mode.
3. **Graceful Failures**: If the configured cloud LLM fails or credentials are missing in production, return an explicit error JSON/SSE payload instead of generating fake mock answers.
4. **Preserved Local Dev**: Local development using Ollama + `qwen2.5:3b` remains completely intact and functional on `http://localhost:3000`.

