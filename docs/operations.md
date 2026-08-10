# NOVA AI — Operational Runbook & Maintenance Guide

This document provides guidelines for daily operations, health monitoring, log investigation, performance tuning, and incident response.

---

## 1. System Architecture Overview

- **Nginx Reverse Proxy**: Port `80` (SSL Termination, static content & request routing)
- **Frontend App (Next.js)**: Port `3000` (SSR, Turbopack, UI client)
- **Backend API (FastAPI)**: Port `8000` (Async SSE streams, AI Router, Agent Engine, Worker)
- **PostgreSQL Database**: Port `5432` (`pgvector` vector storage, Relational tables)
- **Redis Cache & State**: Port `6379` (Rate limits, Distributed locks, Job Queue, Circuit Breaker)
- **Prometheus**: Port `9090` (Metrics collection)
- **Grafana**: Port `3005` / `3001` (Observability dashboards)

---

## 2. Health & Readiness Monitoring

The backend exposes two standardized health endpoints:

- `GET /health`: Liveness probe (Returns HTTP 200 `{ "status": "ok" }`).
- `GET /ready` or `GET /readiness`: Readiness probe (Validates DB and Redis connections).

### Healthcheck Command:
```bash
curl -i http://localhost:8000/ready
```

---

## 3. Log Investigation & Correlation IDs

Backend logs use structured JSON with automatic `X-Request-ID` injection for request tracing.

### Tail Backend Logs:
```bash
docker compose logs -f --tail=100 backend
```

### Search Log by Request ID:
```bash
docker compose logs backend | grep "req_abc123"
```

---

## 4. Incident Response Runbooks

### Incident 1: High Latency or Upstream LLM Errors
1. Check Circuit Breaker state in Grafana panel `LLM Circuit Breaker Status`.
2. Inspect upstream provider errors in logs:
   ```bash
   docker compose logs backend | grep "CircuitBreaker"
   ```
3. If primary provider fails, backend automatically fails over to secondary or mock provider.

### Incident 2: Redis Disconnection
1. Check Redis health:
   ```bash
   docker exec nova-redis redis-cli ping
   ```
2. If Redis is down, backend gracefully falls back to thread-safe in-memory caching and local asyncio locks (`local-fallback`).
3. Restart Redis:
   ```bash
   docker compose restart redis
   ```

### Incident 3: Database Connection Exhaustion
1. Check active database connections:
   ```bash
   docker exec -it nova-postgres psql -U postgres -d nova_ai -c "SELECT count(*) FROM pg_stat_activity;"
   ```
2. Increase SQLAlchemy pool size in `backend/app/db/database.py` if needed.
