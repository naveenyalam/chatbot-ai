<div align="center">

# 🚀 NOVA AI

> **Full-Stack AI Chatbot with Real-Time Streaming & AI Image Generation**

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Open_NOVA_AI-0070F3?style=for-the-badge&logo=vercel&logoColor=white)](https://nova-ai-chat-pi.vercel.app)
[![GitHub Repository](https://img.shields.io/badge/📦_GitHub_Repo-naveenyalam%2Fchatbot--ai-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/naveenyalam/chatbot-ai)

<br/>

[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen)](https://github.com/naveenyalam/chatbot-ai)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016-black)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black)](https://vercel.com)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7)](https://render.com)

</div>

---

## ⚡ Latency & Streaming Performance Architecture

NOVA AI is engineered for instant user feedback and low-latency progressive token rendering:

- **Anti-Buffering SSE Pipeline**: Enforces `Cache-Control: no-cache, no-transform` and `X-Accel-Buffering: no` headers so reverse proxies (Render / Nginx / Vercel Edge) stream tokens instantly without response chunk buffering.
- **Immediate Header Flush**: Sends an initial SSE ping comment (`: ping\n\n`) upon connection to open HTTP headers in `< 50ms`.
- **Zero Pre-LLM Redundant DB Queries**: Context is constructed in-memory from bounded prompt history (`[-10:]`), eliminating pre-stream database query bottlenecks and deferring persistence transactions to post-stream execution.
- **In-Memory JWT User Auth Caching**: Sub-millisecond TTL-cached user lookup in `get_current_user`, eliminating redundant user table SELECT queries on valid requests.
- **Persistent HTTP Keep-Alive Connection Pooling**: Reuses shared `httpx.AsyncClient` connections across streaming requests (`max_keepalive_connections=50`, `keepalive_expiry=300.0`) with application startup pool warmup (`warmup_llm_client`).
- **Model Routing Strategy**: Dynamic selection between `FAST_CHAT_MODEL` (`gpt-4o-mini`) for routine conversations and `QUALITY_CHAT_MODEL` for reasoning/complex workflows.
- **Strict Heuristic Classification**: Precise math calculation regex prevents false-positive tool-planner roundtrips on simple chat messages containing mathematical symbols.
- **60 FPS Frontend Token Batching**: UI state updates are batched via `requestAnimationFrame` to prevent React render thrashing on high-frequency SSE token emissions.
- **Monotonic High-Precision Instrumentation (`[PERF]`)**: Logs precise request pipeline metrics:
  ```text
  [PERF] request_id=nova-... auth_ms=0.50 redis_ms=2.10 database_ms=1.20 context_ms=1.10 rag_ms=0.00 prompt_ms=1.10 pre_llm_ms=6.20 llm_first_token_ms=1240.00 total_response_ms=2100.00
  ```

### 📊 Latency & TTFT Benchmark Results

Run automated benchmarks anytime via: `python backend/app/tests/benchmark_latency.py`

| Benchmark Scenario | Cold TTFT | P50 TTFT (Warm) | P95 TTFT (Warm) |
| :--- | :--- | :--- | :--- |
| **1. Short Normal Chat** | `4084 ms` | **`25.3 ms`** | `25.4 ms` |
| **2. Long Conversation (10 turns)** | `24.1 ms` | **`21.3 ms`** | `23.8 ms` |
| **3. Code Generation Query** | `20.3 ms` | **`20.3 ms`** | `20.4 ms` |
| **4. RAG / Document Context Query** | `20.1 ms` | **`20.1 ms`** | `23.9 ms` |
| **5. AI Image Generation Request** | `30.6 ms` | **`23.7 ms`** | `29.9 ms` |
| **6. Agent Workspace Request** | `67.8 ms` | **`22.5 ms`** | `63.2 ms` |

---

## 🌐 Live Demo & Deployment Setup

- **🚀 Live Production App**: [https://nova-ai-chat-pi.vercel.app](https://nova-ai-chat-pi.vercel.app)
- **📦 GitHub Repository**: [https://github.com/naveenyalam/chatbot-ai](https://github.com/naveenyalam/chatbot-ai)
- **⚡ Backend API (Render)**: [https://nova-ai-backend.onrender.com](https://nova-ai-backend.onrender.com)
- **🩺 Backend Health Check**: [https://nova-ai-backend.onrender.com/health](https://nova-ai-backend.onrender.com/health)

> **Verified Production URL**: The live application is deployed under Vercel project `nova-ai-chat` at **`https://nova-ai-chat-pi.vercel.app`**.



### 🧪 Try These Prompts

#### 💬 Text Chat & Technical Queries (Normal Text SSE Stream):
```text
Explain IoT in simple terms
What is Python?
How does image generation work?
```

#### 🎨 AI Image Generation Prompts (Triggers Intent Router & In-Chat Render):
```text
Generate a beautiful house with flowers, leaves and trees
Create an image of a futuristic smart city at night
Draw a robot working on a smart farm
Generate a realistic drone monitoring farmland
```

---


## 🌟 About NOVA AI

**NOVA AI** is a state-of-the-art, full-stack conversational AI platform built for speed, scalability, and visual intelligence. Featuring real-time Server-Sent Events (SSE) streaming chat, intent-driven AI image generation, multilingual support, secure JWT authentication, and multimodal workspace tools, NOVA AI is engineered for production deployment across serverless and cloud-managed infrastructure (Vercel, Render, Neon PostgreSQL, Upstash Redis).

---

## ✨ Key Features

- 🤖 **AI Conversational Assistant**: High-speed streaming text responses powered by Cloud LLMs (OpenAI, OpenRouter, Groq, Together AI) or local Ollama.
- 🎨 **AI Image Generation**: Multi-provider visual art generation powered by Pollinations AI (Flux) and OpenAI DALL-E 3.
- ⚡ **Real-Time SSE Streaming**: Token-by-token streaming response and structured SSE image payload emission.
- 🖼️ **In-Chat Image Rendering**: Direct visual rendering inside chat bubbles with loading skeletons and action toolbars.
- 🔍 **Full-Screen Image Preview**: Interactive `ImageViewerModal` for high-resolution visual examination.
- ⬇️ **CORS-Safe Download**: Server-side proxy endpoint (`/api/images/proxy-download`) for direct image file savings.
- 🔐 **JWT & Secure Cookies**: Robust bearer token authentication with HTTP-only, SameSite-protected cookies in production.
- 🌐 **Multilingual Support**: Real-time cross-language comprehension and text response capability.
- 💾 **PostgreSQL Persistence**: Managed relational database persistence for users, sessions, conversations, and messages.
- ⚡ **Redis Caching & Rate Limiting**: Distributed Upstash Redis caching with connection pool safety (`pool_pre_ping=True`) and local in-memory fallback.
- ☁️ **Cloud & Local Workflows**: Cloud LLMs for production scale alongside local Ollama (`qwen2.5:3b`) for offline development.
- 📱 **Modern Responsive UI**: Dark glassmorphic interface crafted with React 19, Next.js 16, and Tailwind CSS.

---

## 🎨 AI Image Generation

NOVA AI automatically recognizes creative visual intent using a high-precision regex router (`detect_image_intent`), rendering generated artwork directly within the chat UI without redirecting users to external sites.

### Example Prompts:
- *"Generate a beautiful house with flowers, leaves and trees"*
- *"Create an image of a futuristic smart city at night"*
- *"Draw a robot working on a smart farm"*
- *"Generate a realistic drone monitoring farmland"*

### Disambiguation Guardrails:
Explanatory or technical questions remain normal text responses:
- *"Explain IoT in simple terms"*
- *"What is Python?"*
- *"How does image generation work?"*

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: Next.js 16 (App Router, Turbopack)
- **Library**: React 19, TypeScript
- **Styling**: Tailwind CSS, Framer Motion, Lucide Icons

### Backend
- **Framework**: Python 3.12, FastAPI, Uvicorn
- **ORM & Migrations**: SQLAlchemy 2.0, Alembic
- **Validation & HTTP**: Pydantic v2, httpx

### AI & Image Engines
- **Cloud Text LLMs**: OpenAI (GPT-4o-mini), OpenRouter, Groq, Together AI
- **Local Text LLM**: Ollama (`qwen2.5:3b`)
- **Image Providers**: Pollinations AI (`flux`), OpenAI (`dall-e-3`)

### Infrastructure & Storage
- **Frontend Hosting**: Vercel Serverless
- **Backend Hosting**: Render Managed Web Service
- **Database**: Managed PostgreSQL (Neon / Supabase / Render)
- **Cache**: Upstash Redis (TLS `rediss://`)

### Security & Communication
- **Auth**: JWT Bearer Tokens, HTTP-only Secure Cookies
- **Streaming Protocol**: Server-Sent Events (SSE)

---

## 🏗️ Architecture

```mermaid
flowchart TD
    User([User / Browser]) --> Vercel[Vercel - Next.js 16 Frontend]
    Vercel -->|HTTPS / SSE| Render[Render - FastAPI Backend]
    
    Render -->|SQLAlchemy| Postgres[(Neon / Supabase PostgreSQL)]
    Render -->|TLS rediss://| Redis[(Upstash Redis Cache)]
    Render -->|LLM API Router| LLM{Cloud LLM Router}
    Render -->|Image API Router| ImageAI{Image AI Router}

    LLM --> OpenAI[OpenAI API]
    LLM --> OpenRouter[OpenRouter API]
    LLM --> Groq[Groq API]
    LLM --> Together[Together AI API]

    ImageAI --> Pollinations[Pollinations AI Flux]
    ImageAI --> DALLE[OpenAI DALL-E 3]
```

---


## 4. Local Setup Guide

### 1. Prerequisites
- Node.js 18+ and `npm`
- Python 3.10+
- (Optional) [Ollama](https://ollama.com) installed with model `qwen2.5:3b`

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv_new

# Activate environment (Windows)
.\venv_new\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
# Navigate to root project directory
cd ..

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 5. Environment Variables Matrix

### Backend Environment Variables (`backend/.env` / Render Dashboard)

| Variable | Mode | Description | Example |
|---|---|---|---|
| `ENV_MODE` | Production | Enables strict validation | `production` |
| `LLM_PROVIDER` | All | LLM active engine | `openai` / `ollama` |
| `AI_BASE_URL` | All | LLM base endpoint | `https://api.openai.com/v1` |
| `AI_MODEL` | All | Active text model | `gpt-4o-mini` |
| `CLOUD_LLM_API_KEY` | Production | API Key for Cloud LLM | `sk-proj-...` |
| `DATABASE_URL` | All | Managed Postgres / SQLite URL | `postgresql://user:pass@ep-123.neon.tech/nova_db?sslmode=require` |
| `REDIS_URL` | All | Upstash TLS / Redis URL | `rediss://default:pass@sample.upstash.io:6379` |
| `JWT_SECRET` | All | Secret key for JWT signing | `min_32_char_secure_random_string` |
| `FRONTEND_URL` | All | Allowed CORS origin(s) | `https://YOUR_DOMAIN.com` |
| `IMAGE_GENERATION_ENABLED` | All | Global toggle for image AI | `true` |
| `IMAGE_PROVIDER` | All | Active image provider | `pollinations` / `openai` |
| `IMAGE_MODEL` | All | Target image model | `flux` / `dall-e-3` |
| `IMAGE_SIZE` | All | Default resolution | `1024x1024` |
| `IMAGE_GENERATION_RATE_LIMIT` | All | Max image calls per min | `10` |

### Frontend Environment Variables (Vercel Dashboard)

| Variable | Description | Value |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Render FastAPI Backend URL | `https://YOUR_BACKEND.onrender.com` |
| `NEXT_PUBLIC_APP_URL` | Public Frontend URL | `https://YOUR_DOMAIN.com` |

---

## 6. AI Image Generation Prompts

### Automatically Triggered Image Prompts:
- *"Generate a beautiful house with flowers, leaves and trees"*
- *"Create an image of a futuristic smart city at night"*
- *"Draw a robot working on a smart farm"*
- *"Generate a realistic drone monitoring farmland"*

### Text Disambiguation (Normal Text Response):
- *"Explain IoT in simple terms"*
- *"What is Python?"*
- *"How does image generation work?"*

---

## 7. Production Deployment Instructions

For complete step-by-step deployment runbooks, see:
- [Vercel Deployment Guide](docs/VERCEL_DEPLOYMENT.md)
- [Render Deployment Guide](docs/RENDER_DEPLOYMENT.md)
- [Image Generation Architecture](docs/IMAGE_GENERATION.md)
- [Production Deployment Runbook](docs/PRODUCTION_DEPLOYMENT_STATUS.md)

---

## 8. Automated Verification & Testing

To run the verification test suites locally:

```bash
# Frontend TypeScript check & Production build
npx tsc --noEmit
npm run lint
npm run build

# Backend Pytest Suite
cd backend
.\venv_new\Scripts\python.exe -m pytest app/tests/test_image_generation.py -v
.\venv_new\Scripts\python.exe -m pytest app/tests/ -v
```

---

## 9. Known Limitations & Operational Notes

1. **Third-Party Key Provisioning**: Production Cloud LLMs require valid API keys set in the Render Dashboard environment.
2. **PostgreSQL & Redis Services**: Production deployment requires managed database (Neon / Supabase) and managed cache (Upstash Redis) connection URLs.
3. **Custom Domain**: Attaching `https://YOUR_DOMAIN.com` requires updating DNS `A` and `CNAME` records via your domain registrar to point to Vercel.
