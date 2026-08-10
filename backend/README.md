# NOVA AI - FastAPI Backend Service

This is the backend orchestration service for **NOVA AI**, built with FastAPI. It handles routing requests to the AI LLM provider, manages system instruction parameters, validates schemas, logs activities, and handles active browser stream terminations.

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── chat.py          # Post chat streaming endpoint
│   ├── core/
│   │   ├── config.py           # Configuration models
│   │   └── security.py         # Protection utilities
│   ├── schemas/
│   │   └── chat.py             # Chat validation schemas
│   ├── services/
│   │   ├── ai_service.py       # Centralized instructions & model mapper
│   │   └── llm_provider.py     # Base & OpenAI streaming providers
│   └── main.py                 # Core app & CORS middleware setup
├── .env.example
├── requirements.txt
└── README.md
```

## Setup & Running Local Development

### 1. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in the parameters (API Keys and Models). If `AI_API_KEY` is omitted, the server operates on a mock streaming fallback engine to enable quick onboarding.

### 2. Setup Virtual Environment & Dependencies
Initialize and activate your environment:
```bash
python -m venv venv
```
* **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

Install packages:
```bash
pip install -r requirements.txt
```

### 3. Run FastAPI Application
Start the Uvicorn reload server on port `8000`:
```bash
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

- **`GET /health`**: Health status diagnostic. Returns `{"status": "ok", "service": "nova-ai-backend"}`.
- **`POST /api/chat/stream`**: Returns SSE streaming chunks representing token emissions.
  - Body:
    ```json
    {
      "messages": [
        {"role": "user", "content": "Explain quantum superposition"}
      ],
      "model": "nova-intelligence",
      "temperature": 0.7
    }
    ```
