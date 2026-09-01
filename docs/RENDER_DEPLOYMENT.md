# Render FastAPI Backend Deployment Guide

This guide details how to deploy the **NOVA AI** FastAPI backend service to **Render** without a VPS or self-hosted server.

---

## 1. Service Prerequisites
1. A free or paid account on [Render](https://render.com).
2. A managed PostgreSQL database (e.g. [Neon](https://neon.tech), Supabase, or Render Postgres).
3. A managed Redis instance (e.g. [Upstash](https://upstash.com)).
4. An API key from a Cloud LLM provider (OpenAI, OpenRouter, Groq, Together AI).

---

## 2. Render Web Service Setup

### Step 1: Create Web Service
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your `chatbot-ai` repo.

### Step 2: Configure Service Settings
* **Name**: `nova-ai-backend`
* **Region**: Choose closest to users (e.g. Singapore, Oregon, Frankfurt)
* **Branch**: `main` (or your primary branch)
* **Root Directory**: `backend` (or leave default if using Blueprint)
* **Runtime**: Python 3
* **Build Command**: `pip install -r backend/requirements.txt`
* **Start Command**: `cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
* **Health Check Path**: `/health`

---

## 3. Environment Variables Configuration

In the **Environment** tab on Render, add the following variables:

| Key | Example Value | Description |
| --- | --- | --- |
| `ENV_MODE` | `production` | Enables strict validation (rejects weak JWT secrets and SQLite) |
| `LLM_PROVIDER` | `openai` | Cloud LLM identifier (`openai`, `openrouter`, `groq`, `together`) |
| `AI_BASE_URL` | `https://api.openai.com/v1` | Cloud provider base URL |
| `AI_MODEL` | `gpt-4o-mini` | Cloud model name |
| `CLOUD_LLM_API_KEY` | `sk-proj-...` | Provider API Key |
| `DATABASE_URL` | `postgresql://user:pass@ep-123.neon.tech/nova_db?sslmode=require` | Managed Postgres URL |
| `REDIS_URL` | `rediss://default:pass@sample.upstash.io:6379` | Upstash TLS Redis URL |
| `JWT_SECRET` | *(32+ character random string)* | JWT signing secret |
| `FRONTEND_URL` | `https://YOUR_DOMAIN.com` | Allowed CORS origin |
| `SECURE_COOKIES` | `true` | Enforces HTTPS-only cookies |

---

## 4. Verification

After deployment:
1. Access `https://nova-ai-backend.onrender.com/health`.
2. Confirm the JSON payload returns `"status": "healthy"`.
