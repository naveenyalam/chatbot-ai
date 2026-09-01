# NOVA AI — Production AI Image Generation Documentation

This document describes the architectural setup, configuration, API endpoints, intent router, and UI components for AI Image Generation in NOVA AI.

---

## 1. Overview & Topology

NOVA AI supports multi-provider AI Image Generation (Pollinations AI and OpenAI DALL-E 3) to render high-resolution AI artwork and graphics directly inside the chat interface.

- **Frontend Hosting**: Vercel
- **Backend Hosting**: Render
- **Database**: Managed PostgreSQL (Neon / Supabase / Render Postgres)
- **Redis**: Managed Upstash Redis
- **LLM Provider**: Cloud LLM Provider (OpenAI / OpenRouter / Groq) or Local Ollama
- **Image Generation Provider**: `IMAGE_PROVIDER` (`pollinations` or `openai`)

```
[Chat Composer] / [Natural Prompt]
        │
        ▼
[Intent Detection Router]
  detect_image_intent(prompt)
        │
        ├── Text Chat ──► [Workspace AI Engine] ──► SSE Token Stream
        │
        └── Image Intent ──► [POST /api/workspaces/{mode}/chat]
                                    │
                                    ▼
                         [BaseImageProvider]
                 (Pollinations / OpenAI DALL-E 3)
                                    │
                                    ▼
                         [ImageMessage UI Card]
                                    │
                                    ├── [Expand] ──► ImageViewerModal
                                    └── [Download] ──► /api/images/proxy-download
```

---

## 2. Configuration Settings

Image generation settings are managed in `backend/app/core/config.py` and fully controlled via environment variables:

| Variable | Default | Description |
|---|---|---|
| `IMAGE_GENERATION_ENABLED` | `true` | Enables or disables AI image generation globally |
| `IMAGE_PROVIDER` | `pollinations` | Active provider (`pollinations` or `openai`) |
| `IMAGE_MODEL` | `flux` | Model identifier (`flux` for Pollinations, `dall-e-3` for OpenAI) |
| `IMAGE_API_KEY` | *(Configurable)* | API key for configured provider (not required for Pollinations) |
| `IMAGE_SIZE` | `1024x1024` | Default resolution (`1024x1024`) |
| `IMAGE_GENERATION_RATE_LIMIT` | `10` | Maximum image requests allowed per user per minute |
| `IMAGE_GENERATION_MAX_PROMPT_LENGTH` | `1000` | Maximum allowed prompt character length |

---

## 3. Intent Router & Prompt Disambiguation

Natural language prompts are scanned by `detect_image_intent(prompt)` in `backend/app/services/image_intent_router.py`.

### Automatically Triggered Image Prompts:
- *"Generate a beautiful house with flowers, leaves and trees"*
- *"Create an image of a futuristic smart city at night"*
- *"Draw a robot working on a smart farm"*
- *"Generate a realistic drone monitoring farmland"*
- *"/image A glowing crystal skull"*

### Non-Image Prompts (Routed to Normal Text Chat):
- *"Explain IoT in simple terms"*
- *"What is Python?"*
- *"How does image generation work?"*
- *"How to create an image element in React"*

---

## 4. Local Development & Production Safety

1. **Vercel & Render Integration**: Zero server dependencies required.
2. **Local Ollama Independence**: Local Ollama setup remains completely independent for text chat (`qwen2.5:3b`).
3. **Secret Security**: API keys are passed through environment variables and never committed or leaked in client responses or logs.

---

## 5. Security & Isolation Rules

1. **No VPS Requirement**: Runs seamlessly on Render + Vercel serverless environments.
2. **Key Security**: API keys are injected via environment variables (`CLOUD_LLM_API_KEY`) and are never exposed to client browsers or Git repositories.
3. **Local Development Safety**: Ollama text chat remains default locally (`qwen2.5:3b`). If cloud API keys are not supplied during local dev, image requests fail gracefully with user-facing alerts without breaking text chat.
