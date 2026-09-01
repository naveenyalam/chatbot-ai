<div align="center">

# 🚀 NOVA AI

> **Full-Stack AI Chatbot with Real-Time Streaming & AI Image Generation**

[![Target Demo](https://img.shields.io/badge/🌐_Demo-Target_Deployment_URL-0070F3?style=for-the-badge&logo=vercel&logoColor=white)](https://chatbot-ai.vercel.app)
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

## 🚀 Deployment & Live App Setup

- **GitHub Repository**: [https://github.com/naveenyalam/chatbot-ai](https://github.com/naveenyalam/chatbot-ai)
- **Target Frontend URL (Vercel)**: `https://<your-project-name>.vercel.app`
- **Target Backend URL (Render)**: `https://<your-project-name>.onrender.com`

> **Note on Live URL**: `chatbot-ai.vercel.app` is currently registered to a separate third-party Vercel project. When you import `https://github.com/naveenyalam/chatbot-ai` into your Vercel account, Vercel generates your own unique public production URL (e.g. `nova-ai-chat.vercel.app`).


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
