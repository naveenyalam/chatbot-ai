# NOVA AI — Production Infrastructure Stack

NOVA AI is a secure, high-performance, containerized web application built with a FastAPI backend and a Next.js frontend. This repository contains the configurations, Dockerfiles, and services orchestration required to run NOVA AI in a production environment.

## 1. Production Architecture

The production environment utilizes a reverse-proxied, multi-service network architecture:

```
                     NOVA AI client
                           │
                     HTTPS / Port 80
                           │
                     ┌─────▼─────┐
                     │   Nginx   │
                     │  Gateway  │
                     └─────┬─────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      ┌──────────────┐            ┌──────────────┐
      │   Next.js    │            │   FastAPI    │
      │   Frontend   │            │   Backend    │
      │ (Port 3000)  │            │ (Port 8000)  │
      └──────────────┘            └──────┬───────┘
                                         │
                               ┌─────────┴─────────┐
                               ▼                   ▼
                        ┌──────────────┐    ┌──────────────┐
                        │  PostgreSQL  │    │    Redis     │
                        │  + pgvector  │    │  Cache/Limit │
                        └──────────────┘    └──────────────┘
```

* **Reverse Proxy (Nginx)**: Routes incoming web traffic (`/` to the Next.js frontend, `/api` and `/docs` to the FastAPI backend). Proxy buffering is disabled specifically on `/api` routes to allow real-time Server-Sent Events (SSE) streaming.
* **Frontend (Next.js)**: Production-built Next.js 16 container running on React 19.
* **Backend (FastAPI)**: Asynchronous REST and streaming API. Performs core chat routing, autonomous RAG search, sandboxed code execution, and user management.
* **Database (PostgreSQL + pgvector)**: Production-grade SQL storage. Relies on the `pgvector/pgvector:pg16` image for embedding and document similarity queries.
* **Cache & Rate Limiting (Redis)**: Shared Redis server for distributed token-bucket rate limiting and session caches, preventing single-point resource starvation.

---

## 2. Environment Configuration

Copy `backend/.env.example` to `backend/.env` (or configure via environment variables directly in the Docker Compose container).

### Environment Parameters

| Variable Name | Type | Description / Default | Mode |
|---|---|---|---|
| `ENV_MODE` | String | `development` or `production` | All |
| `DATABASE_URL` | String | `postgresql://user:pass@host:5432/db` (or SQLite in dev) | All |
| `REDIS_URL` | String | `redis://redis:6379/0` (Required in production) | Prod |
| `AI_API_KEY` | String | LLM Provider API Key (OpenAI, Gemini compatible, etc.) | All |
| `AI_MODEL` | String | LLM model identifier (default: `gpt-4o-mini`) | All |
| `AI_BASE_URL` | String | LLM API provider base endpoint | All |
| `JWT_SECRET` | String | Secure cryptographic token sign key (Min 32 chars) | Prod |
| `RATE_LIMIT_ENABLED` | Boolean | Activates route requests throttling (default: `true`) | All |
| `RATE_LIMIT_REQUESTS`| Integer | Max permitted requests in window (default: `60`) | All |
| `RATE_LIMIT_WINDOW_SECONDS`| Integer | Rate limit time frame window (default: `60`) | All |

> [!IMPORTANT]
> In `production` mode, the backend enforces strict validation: it will refuse to start if using an SQLite database url or if `REDIS_URL` is omitted.

---

## 3. Deployment with Docker Compose

Ensure Docker and Docker Compose are installed on your target server.

### Build and Launch Services
To build and start all containers in detached mode:
```bash
docker compose up --build -d
```

This starts:
1. `nova-postgres` (PostgreSQL with pgvector)
2. `nova-redis` (Redis cache)
3. `nova-backend` (FastAPI backend; automatically runs `alembic upgrade head` migrations first)
4. `nova-frontend` (Next.js frontend)
5. `nova-nginx` (Nginx gateway reverse proxy mapping to external port 80)

### Check Services Health
```bash
docker compose ps
```

### Inspect Container Logs
To monitor logs in real time:
```bash
docker compose logs -f
```

---

## 4. Diagnostics & Probes

The FastAPI backend exposes dedicated health endpoints:

### Health Probe
* **Endpoint**: `GET /health` (or through reverse proxy `/health`)
* **Behavior**: Simple check verifying that the Python application process is up.
* **Return**: `{"status": "ok", "service": "nova-ai-backend"}`

### Readiness Probe
* **Endpoint**: `GET /readiness` (or through reverse proxy `/readiness`)
* **Behavior**: Dependency-aware probe checking:
  1. Connection to PostgreSQL database (via `SELECT 1` execution).
  2. Connection to Redis server (via `PING`).
* **Return**: 
  * `200 OK` if all services are online.
  * `503 Service Unavailable` if PostgreSQL or Redis is offline.

---

## 5. Troubleshooting & Commands

### Database Migrations
Migrations are handled via Alembic. If you need to generate a new migration during local development:
```bash
cd backend
# Create a migration revision
.\venv\Scripts\python -m alembic revision --autogenerate -m "description_of_change"
# Apply migrations locally
.\venv\Scripts\python -m alembic upgrade head
```

### Run Local Unit Tests
Run the pytest suite to verify core logic:
```bash
cd backend
.\venv\Scripts\python -m pytest app/tests/ -v --tb=short
```

### Local Frontend Verification
Verify TypeScript type checks and run local production build:
```bash
# TypeScript Check
npx tsc --noEmit

# Production Build
npm run build
```

## Observability & Monitoring Architecture

NOVA AI integrates production-grade structured JSON logging, request correlation ID tracking, and Prometheus metrics out of the box.

### Telemetry Endpoints
- **Process Liveness**: `/health` (checks if the FastAPI process is alive)
- **Database & Cache Readiness**: `/readiness` (pings PostgreSQL and Redis, returns `503 Service Unavailable` if critical systems are offline)
- **Prometheus Metrics**: `/metrics` (exposes system latency, counters, and errors)

### Logging & Correlation IDs
- Every HTTP request gets a unique, UUID-based correlation ID (via `X-Request-ID` header and context variables).
- Correlation IDs are automatically injected into all logging contexts and response headers.
- **Production Mode**: Output formatted as single-line JSON streams.
- **Development Mode**: Output formatted as human-readable console logs.
- Sensitive authentication details, passwords, and tokens are automatically filtered to avoid leaks.

### Prometheus Metrics Scraped
- **HTTP**: `nova_http_requests_total`, `nova_http_request_duration_seconds`
- **AI/LLM**: `nova_llm_requests_total`, `nova_llm_request_duration_seconds`, `nova_llm_fallbacks_total` (tracks provider failover)
- **Agents**: `nova_agent_runs_total`, `nova_agent_run_duration_seconds`, `nova_tool_calls_total` (tracks tool status)
- **RAG & Search**: `nova_rag_searches_total`, `nova_rag_search_duration_seconds`
- **Infrastructure**: `nova_redis_operations_total`, `nova_db_operations_total`, `nova_redis_cache_hits_total`, `nova_redis_cache_misses_total`

### Grafana Dashboards
Grafana is preconfigured to auto-provision the Prometheus datasource and load a rich monitoring dashboard.
- Grafana port: `3005` (exposed at `http://localhost:3005`)
- Default credentials: `admin` / `admin`

## Documentation

For deep dives into production deployment, cloud launch, performance, migrations, operations, and security, refer to:
- [Phase 17 IDE Error Cleanup Report](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/phase17-error-cleanup.md)
- [Phase 13 Production Operations Report](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/phase13-production-operations.md)
- [Distributed Observability & Tracing Architecture](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/observability.md)
- [Prometheus Alerting Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/alerting.md)
- [Phase 13 Complete UI Audit Report](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/phase13-ui-audit.md)
- [Phase 13 Design System Specification](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/phase13-ui-design-system.md)
- [Phase 13 UI Verification Log](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/phase13-ui-verification.md)
- [Grafana Dashboards Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/grafana.md)
- [AI Quality Evaluation & Grounding Monitoring](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/ai-quality-monitoring.md)
- [RAG Feedback & Evaluation Pipeline](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/rag-feedback.md)
- [Autonomous Failure Recovery Architecture](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/self-healing.md)
- [AI Cost Guardrails & Budget Boundaries](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/ai-cost-guardrails.md)
- [Caching Strategy & Redis Isolation](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/caching-strategy.md)
- [Background Processing Architecture](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/background-jobs.md)
- [Security Anomaly Monitoring](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/security-monitoring.md)
- [Operational Runbooks Directory](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/runbooks/)
- [Phase 12 Performance & Scalability Report](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/phase12-performance-report.md)
- [Performance Baseline Audit](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/performance-baseline.md)
- [Database Performance & Indexing Strategy](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/database-performance.md)
- [RAG Quality Evaluation & Precision Report](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/rag-evaluation.md)
- [LLM Cost Optimization & Cost Model](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/llm-cost-optimization.md)
- [Autonomous Agent Performance Audit](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/agent-performance.md)
- [Load Testing & Scalability Report](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/load-testing.md)
- [Infrastructure Capacity Planning Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/capacity-planning.md)
- [LLM Cost Monitoring & Telemetry Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/cost-monitoring.md)
- [Phase 11 Live Deployment Status Report](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/phase11-live-deployment.md)
- [Production Incident Response & Runbooks](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/incident-response.md)
- [Release v1.0.0 Documentation](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/release-v1.md)
- [Changelog](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/CHANGELOG.md)
- [Phase 10 Security Audit Report](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/phase10-security-audit.md)
- [Phase 10 Cloud Architecture Strategy](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/phase10-cloud-architecture.md)
- [Cloud Provider Setup Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/cloud-provider-setup.md)
- [Domain & TLS / SSL Certificate Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/domain-and-tls.md)
- [Phase 9 Production Deployment Audit](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/phase9-deployment-audit.md)
- [Cloud Deployment & Launch Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/cloud-deployment.md)
- [Database Migration & Alembic Runbook](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/database-migrations.md)
- [Frontend Deployment Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/frontend-deployment.md)
- [Production Smoke Testing Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/production-smoke-tests.md)
- [Production Readiness Audit Report](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/production-readiness.md)
- [Production Deployment Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/production.md)
- [Environment Configuration Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/environment.md)
- [Release Engineering Checklist](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/release-checklist.md)
- [Backup & Disaster Recovery Runbook](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/backup-recovery.md)
- [Operations & Monitoring Runbook](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/operations.md)
- [Security Architecture Guide](file:///c:/Users/Lenovo/OneDrive/Desktop/chatbot%20ai/docs/security.md)

---

## 8. Python Development Environment & IDE Configuration

NOVA AI utilizes a FastAPI backend running inside a Python virtual environment (`backend/venv`). To ensure that VS Code or any other Pyrefly/Pylance editor type checker resolves import packages correctly and excludes transient build/virtual runner cache directories:

### Local Workspace Setup
1. **Python Interpreter**: Point your editor's interpreter to the virtual environment python:
   `backend/venv/Scripts/python.exe`
2. **Pyrefly Boundaries (`pyrefly.toml`)**: Ensure `pyrefly.toml` exists at the project root to set boundaries:
   ```toml
   python-interpreter-path = "backend/venv/Scripts/python.exe"
   project-includes = ["backend/app"]
   project-excludes = [
       "**/__pyrefly_virtual__/**",
       "**/inmemory/**",
       "**/venv/**",
       "**/node_modules/**"
   ]
   ```
3. **Workspace Settings (`.vscode/settings.json`)**: Configure analysis exclusions to ignore virtual directories:
   ```json
   {
     "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/Scripts/python.exe",
     "python.analysis.exclude": [
       "**/__pyrefly_virtual__/**",
       "**/inmemory/**",
       "**/venv/**",
       "**/node_modules/**"
     ]
   }
   ```
