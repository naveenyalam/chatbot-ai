# NOVA AI — Production Deployment Status & Runbook

## 1. Executive Summary

This document serves as the comprehensive production readiness status report and step-by-step deployment runbook for **NOVA AI**. The project has been fully decoupled from local VPS dependencies, self-hosted Docker requirements, and local PC availability.

---

## 2. Architecture Overview

### Production (100% Cloud-Managed & Serverless)
```
User
  ↓
https://YOUR_DOMAIN.com (Vercel Next.js 16)
  ↓
FastAPI on Render (https://YOUR_RENDER_BACKEND.onrender.com)
  ├── Managed PostgreSQL (Neon / Supabase / Render Postgres)
  ├── Upstash Redis (Serverless TLS Cache & Rate Limiting)
  └── Cloud LLM Provider API (OpenAI / OpenRouter / Groq / Together AI)
```

### Local Development (Ollama Stack preserved)
```
http://localhost:3000 (Next.js)
  ↓
http://localhost:8000 (FastAPI)
  ├── SQLite (nova_ai.db)
  └── Ollama (qwen2.5:3b)
```

---

## 3. Deployment Status Summary

| Phase | Component | Status | Description |
| --- | --- | --- | --- |
| 1 | Audit & Architecture | **COMPLETED** | Audited core files & created `NO_VPS_DEPLOYMENT.md` |
| 2 | LLM Provider Abstraction | **COMPLETED** | Implemented `LLM_PROVIDER` abstraction supporting Ollama locally and Cloud LLMs in production |
| 3 | Real-Time SSE Streaming | **COMPLETED** | Preserved native SSE streaming & multilingual token output |
| 4 | AI Image Generation | **COMPLETED** | Intent detection, Pollinations & OpenAI providers, ImageMessage component, download proxy, verified end-to-end |
| 5 | CORS Configuration | **COMPLETED** | Dynamic environment-driven CORS via `FRONTEND_URL` (no wildcard `*` in production) |
| 6 | Frontend API Client | **COMPLETED** | Centralized API client targeting `process.env.NEXT_PUBLIC_API_URL` |
| 7 | Database Migration | **COMPLETED** | SQLAlchemy pooling updated with `pool_pre_ping=True` for managed Postgres |
| 8 | Upstash Redis | **COMPLETED** | Enabled SSL `rediss://` URL support & graceful in-memory fallback |
| 9 | Render Deployment Setup | **COMPLETED** | Created Render Blueprint (`render.yaml`) and entrypoint |
| 10 | Vercel Frontend Setup | **COMPLETED** | Verified TypeScript & Next.js production build (`npm run build`) |
| 11 | Custom Domain Setup | **COMPLETED** | Documented DNS & Vercel domain binding in `VERCEL_DEPLOYMENT.md` |
| 12 | Environment Templates | **COMPLETED** | Updated `.env.example` and `.env.production.example` |
| 13 | Security Audit | **COMPLETED** | Audited secrets isolation & cookies |
| 14 | Remove VPS Dependencies | **COMPLETED** | Application operates 100% serverless/cloud-managed |
| 15 | Automated Testing | **COMPLETED** | `npx tsc`, `npm run build`, and backend pytest suite verified |
| 16 | Final Cloud Launch | **READY FOR DEPLOYMENT** | Code fully verified and ready for cloud deployment |

---

## 4. Required External Accounts

To perform the live cloud deployment, you will need free/paid accounts on:
1. **Vercel** (`https://vercel.com`) — Frontend hosting.
2. **Render** (`https://render.com`) — Backend hosting.
3. **Neon / Supabase** (`https://neon.tech` or `https://supabase.com`) — Managed PostgreSQL.
4. **Upstash** (`https://upstash.com`) — Serverless Redis cache.
5. **OpenAI / OpenRouter / Groq** — Cloud LLM API Key provider.
6. **Domain Registrar** (Namecheap, Cloudflare, GoDaddy, etc.) — For custom domain `https://YOUR_DOMAIN.com`.

---

## 5. Required Environment Variables Matrix

### Render Backend Environment (Set in Render Dashboard)
```env
ENV_MODE=production
LLM_PROVIDER=openai # or openrouter / groq / together
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
CLOUD_LLM_API_KEY=your_actual_cloud_llm_api_key
DATABASE_URL=postgresql://user:password@ep-sample.singapore.aws.neon.tech/nova_db?sslmode=require
REDIS_URL=rediss://default:password@sample.upstash.io:6379
JWT_SECRET=your_generated_32_character_secret_key
FRONTEND_URL=https://YOUR_DOMAIN.com,https://www.YOUR_DOMAIN.com
SECURE_COOKIES=true
```

### Vercel Frontend Environment (Set in Vercel Dashboard)
```env
NEXT_PUBLIC_API_URL=https://YOUR_RENDER_BACKEND.onrender.com
NEXT_PUBLIC_APP_URL=https://YOUR_DOMAIN.com
```

> [!CAUTION]
> Never place `CLOUD_LLM_API_KEY`, `DATABASE_URL`, `REDIS_URL`, or `JWT_SECRET` in Vercel environment variables.

---

## 6. Step-by-Step Deployment Procedure

### Step 1: Deploy Database (Neon / Supabase)
1. Create a PostgreSQL database on Neon (`https://neon.tech`).
2. Copy the connection string (e.g. `postgresql://user:pass@ep-xyz.singapore.aws.neon.tech/nova_db?sslmode=require`).

### Step 2: Deploy Cache (Upstash Redis)
1. Create a Redis database on Upstash (`https://upstash.com`).
2. Copy the Redis TLS URL string (starts with `rediss://`).

### Step 3: Deploy Backend (Render)
1. Connect your GitHub repository to Render (`https://render.com`).
2. Select **New** → **Web Service** or import `render.yaml`.
3. Set Environment to **Python**.
4. Set Build Command: `pip install -r backend/requirements.txt`
5. Set Start Command: `cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables listed in Section 5.
7. Click **Create Web Service**. Note the backend URL (e.g., `https://nova-ai-backend.onrender.com`).

### Step 4: Deploy Frontend (Vercel)
1. Import repository to Vercel (`https://vercel.com`).
2. Add `NEXT_PUBLIC_API_URL` pointing to your Render backend URL.
3. Click **Deploy**.

### Step 5: Attach Custom Domain
1. In Vercel Project Settings → **Domains**, add `YOUR_DOMAIN.com`.
2. Add `A` record `76.76.21.21` and `CNAME` record `cname.vercel-dns.com` in your DNS registrar.
3. Update `FRONTEND_URL` on Render with `https://YOUR_DOMAIN.com` once live.

---

## 7. Rollback Procedure

If a production release encounters errors:
1. **Render Backend Rollback**: Go to Render Dashboard → Service → **Deploys** → Select previous successful build → **Rollback**.
2. **Vercel Frontend Rollback**: Go to Vercel Dashboard → **Deployments** → Select previous deployment → **Promote to Production**.
3. Local development can always be executed independently with `npm run dev` and python uvicorn.
