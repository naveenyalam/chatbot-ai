# NOVA AI — Production Release Checklist

Before releasing NOVA AI to production, verify each item on this checklist.

---

## 1. Application & Core Code
- [x] All 68 backend unit, integration, security, and E2E tests pass (`pytest app/tests`).
- [x] Next.js frontend TypeScript type check passes (`npx tsc --noEmit`).
- [x] Next.js production build succeeds (`npm run build`).
- [x] End-to-end user authentication, registration, and JWT lifecycle verified.
- [x] Multi-tenant data isolation verified across conversations, messages, and documents.
- [x] Streaming chat response handling verified over SSE.
- [x] RAG vector indexing and context boundary defenses verified.
- [x] Autonomous agent execution and tool policy limits verified.
- [x] Python code execution sandbox security restrictions verified.

---

## 2. Infrastructure & Containers
- [x] `docker-compose.yml` validated via `docker compose config`.
- [x] Dockerfile healthchecks configured for frontend, backend, postgres, redis, prometheus, and grafana.
- [x] Restart policies set to `always` or `unless-stopped`.
- [x] Persistent volumes configured for PostgreSQL, Redis, Prometheus, Grafana, and backend document storage.
- [x] Background job queue worker active in FastAPI lifespan startup.

---

## 3. Security Hardening
- [x] Environment secrets managed outside source control (`.env.example` committed, `.env` gitignored).
- [x] `JWT_SECRET` generated with high-entropy 32+ character key.
- [x] CORS allowed origins strictly configured (`FRONTEND_URL`).
- [x] Password hashing using Passlib with bcrypt / PBKDF2 algorithm.
- [x] Rate limiting active for auth, chat, documents, and API routes.
- [x] Prompt injection context boundary defenses verified.

---

## 4. Observability & Monitoring
- [x] `/metrics` Prometheus endpoint active and returning custom `nova_*` metrics.
- [x] `/health` and `/ready` endpoints active and returning dependency statuses.
- [x] Structured JSON logging with `X-Request-ID` correlation tracking.
- [x] Grafana dashboard provisioned with panels for RAG cache hits, retrieval latency, LLM retries, and agent limits.

---

## 5. Recovery & Documentation
- [x] Database backup and restore procedures documented (`docs/backup-recovery.md`).
- [x] Operations runbook created (`docs/operations.md`).
- [x] Environment configuration guide created (`docs/environment.md`).
- [x] System production architecture documented (`docs/production.md`).
