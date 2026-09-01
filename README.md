# NOVA AI — AI Chatbot & Multi-Provider Image Generation Platform

[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen)](https://github.com/naveenyalam/chatbot-ai)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016-black)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black)](https://vercel.com)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7)](https://render.com)

**NOVA AI** is an enterprise-grade AI chatbot platform featuring real-time Server-Sent Events (SSE) chat streaming, intent-driven AI image generation, multimodal workspace tools, autonomous agent sandboxing, and high-performance search capabilities.

- **GitHub Repository**: [https://github.com/naveenyalam/chatbot-ai](https://github.com/naveenyalam/chatbot-ai)

---

## 1. Features & Capabilities

- **Real-Time Streaming Chat**: Multilingual SSE streaming text interface powered by Cloud LLMs or local Ollama.
- **Intent-Driven AI Image Generation**: Natural language prompt detection automatically routes visual queries to Pollinations AI or OpenAI DALL-E 3, rendering images directly inside the chat UI with hover controls, full-screen modal previews, and CORS-safe attachment downloads.
- **Disambiguation Guardrails**: Prompt intent router ensures explanatory queries (e.g. *"How does image generation work?"*, *"Explain IoT"*, *"What is Python?"*) remain normal text responses.
- **Workspace Modes**: Specialized agents for General Q&A, Research & Deep Search, Writing & Content Creation, Code Execution & Analysis, Document RAG, and Autonomous Tool Workflows.
- **Serverless/Cloud Managed Deployment**: Fully decoupled from VPS requirements, running on Vercel (Frontend), Render (FastAPI Backend), Neon/Supabase (PostgreSQL), and Upstash (Redis).

---

## 2. Architecture Overview

### Managed Cloud Production Architecture (100% Serverless & Cloud-Managed)
```
User / Browser
      │
      ▼
https://YOUR_APP.vercel.app / https://YOUR_DOMAIN.com (Vercel Next.js 16)
      │
      ▼ (HTTPS / SSE Streaming)
FastAPI Backend on Render (https://YOUR_BACKEND.onrender.com)
      ├── Managed PostgreSQL (Neon / Supabase / Render Postgres)
      ├── Upstash Redis (Serverless TLS Cache & Rate Limiter)
      ├── Cloud LLM Provider (OpenAI / OpenRouter / Groq / Together)
      └── AI Image Provider (Pollinations AI / OpenAI DALL-E 3)
```

### Local Development Architecture (Independent Ollama Stack)
```
http://localhost:3000 (Next.js)
      │
      ▼
http://localhost:8000 (FastAPI)
      ├── SQLite (nova_ai.db)
      ├── In-Memory Cache Fallback
      └── Ollama (qwen2.5:3b)
```

---

## 3. Technology Stack

- **Frontend**: React 19, Next.js 16 (App Router, Turbopack), Tailwind CSS, Lucide Icons, TypeScript.
- **Backend**: Python 3.12, FastAPI, Asyncio, Pydantic v2, SQLAlchemy 2.0, Alembic, httpx.
- **Database & Cache**: Managed PostgreSQL with connection pooling (`pool_pre_ping=True`), Upstash Redis.
- **AI & ML**: OpenAI API, OpenRouter, Groq, Pollinations AI, Ollama (Local).

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
