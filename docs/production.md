# Production Deployment Guide — NOVA AI (Phase 8.6 Release)

This guide documents the procedures and configurations required to deploy the NOVA AI application stack in a secure, performant, and reliable production environment.

---

## 1. Stack Architecture

The production architecture consists of:
- **Nginx Reverse Proxy**: Edge routing, SSL termination, static asset delivery (`nova-nginx:80`).
- **Next.js Frontend**: React Server Components & UI interface (`nova-frontend:3000`).
- **FastAPI Backend**: Asynchronous API core, streaming chat router, background job queue worker (`nova-backend:8000`).
- **PostgreSQL (`pgvector`)**: Production relational database with native vector similarity search (`nova-postgres:5432`).
- **Redis 7+**: In-memory cache, distributed locks, rate-limit buckets, circuit breaker state (`nova-redis:6379`).
- **Prometheus**: Metrics collection & scraping engine (`nova-prometheus:9090`).
- **Grafana**: Visual observability dashboard (`nova-grafana:3005`).

---

## 2. Health & Readiness Verification

Production orchestrators (Kubernetes / Docker Swarm / Cloud services) use two dedicated endpoints:

- `GET /health`: Liveness probe (Verifies application process is running).
- `GET /ready` (or `/readiness`): Readiness probe (Verifies PostgreSQL & Redis connectivity).

---

## 3. Recommended Production Configurations

### Database Pooling
Configure connection pooling parameters in `.env`:
```env
DB_POOL_SIZE=20          # Base connection pool size
DB_MAX_OVERFLOW=50       # Maximum extra connections allowed during traffic spikes
DB_POOL_TIMEOUT=30       # Wait time (seconds) to acquire database connections
DB_POOL_RECYCLE=1800     # Time (seconds) before recycling existing connections
```

### Redis Network & Circuit Breaker Tuning
```env
REDIS_TIMEOUT=2.0        # Socket connection timeout (seconds)
LLM_CIRCUIT_FAILURE_THRESHOLD=5
LLM_CIRCUIT_COOLDOWN_SECONDS=60
```

### API Rate Limiter Thresholds
```env
RATE_LIMIT_AUTH=5        # Limit auth routes to 5 requests per minute
RATE_LIMIT_CHAT=30       # Limit streaming chats to 30 requests per minute
RATE_LIMIT_UPLOAD=10     # Limit uploads to 10 files per minute
RATE_LIMIT_AGENT=10      # Limit agent loops to 10 runs per minute
RATE_LIMIT_GENERAL=120   # General API endpoints rate limit
```

---

## 4. Production Deployment Command

To deploy the entire production stack:

```bash
docker compose config
docker compose build
docker compose up -d
```
