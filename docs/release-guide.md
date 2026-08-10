# NOVA AI Platform Production Release & Deployment Guide

This guide describes how to configure, run, and troubleshoot the NOVA AI Enterprise workspace in a production environment.

---

## 1. Environment Configurations
Production requires two separate `.env` configs.

### Backend Configurations (`backend/.env`)
```ini
# Core Environment Settings
ENV_MODE=production
SECRET_KEY=super-secret-signature-key-rotate-in-production
DATABASE_URL=sqlite:///nova_ai.db

# LLM Providers Configuration
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Rate Limiting & Performance Cache
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_PER_MINUTE=60
```

### Frontend Configurations (`.env.production`)
```ini
# Production API endpoint
NEXT_PUBLIC_API_URL=https://api.nova-ai.local
```

---

## 2. Manual Deployment Steps

### Step A: Backend Services Setup
1. **Virtual Environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Database Migrations**:
   ```bash
   alembic upgrade head
   ```
3. **Execute Production Server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Step B: Frontend Build & Serve
1. **Install Dependencies**:
   ```bash
   npm install
   ```
2. **Build static bundles**:
   ```bash
   npm run build
   ```
3. **Serve Next.js Server**:
   ```bash
   npm run start
   ```

---

## 3. Docker Support (Compose Deployment)
For single-command container deployments, use the root level `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///nova_ai.db
      - ENV_MODE=production
    volumes:
      - backend-storage:/backend/storage

  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000

volumes:
  backend-storage:
```

Launch with:
```bash
docker-compose up --build -d
```

---

## 4. Troubleshooting & Verification Checks
*   **Healthcheck endpoint**: Check `GET /health` or `GET /readiness` to verify API and database connectivity status.
*   **Session Expiry Traps**: If token expiration causes client side failure, check browser console log networks for `401 Unauthorized`. The app will auto-redirect user accounts back to `/login`.
*   **Code Sandbox Errors**: If agent code execution fails, verify target machine dependencies match those defined in `RestrictedPython` configurations.
