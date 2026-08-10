# NOVA AI — Release v1.0.0 Documentation

This document serves as the official release guide for **NOVA AI v1.0.0**.

---

## 1. Release Overview

NOVA AI v1.0.0 is a enterprise-ready, multi-tenant AI conversational platform featuring FastAPI async services, Next.js 16 frontend, PostgreSQL + pgvector vector search, Redis rate limiting, autonomous tool agents, sandboxed code execution, and real-time SSE token streaming.

---

## 2. Key Architectural Features

- **Asynchronous Chat & SSE Streaming**: Real-time character-by-character streaming over HTTP/2 using Server-Sent Events with unbuffered Nginx proxy handling.
- **RAG Vector Search**: Document chunking and pgvector similarity retrieval with strict multi-tenant user isolation.
- **Autonomous Agents**: ReAct agent loop supporting calculator, document search, web search, and Python code execution inside RestrictedPython sandboxes.
- **AI Provider Resiliency**: Circuit breaker pattern with automatic failover between primary and secondary LLM endpoints.
- **Full Telemetry**: Prometheus `/metrics` exporter and pre-provisioned Grafana monitoring dashboards.

---

## 3. Environment & Configuration Requirements

- **Production Mode**: Set `ENV_MODE=production` in `.env`.
- **JWT Secret**: Set `JWT_SECRET` to a 32+ character random string.
- **Database URL**: Production PostgreSQL string (`postgresql://user:pass@host:5432/dbname`).
- **Redis URL**: Required Redis endpoint (`redis://` or `rediss://`).
- **AI API Key**: Valid LLM provider API key (`AI_API_KEY`).

---

## 4. Rollback Safeguards

If a rollback is required post-release:
1. **Database Rollback**: `docker exec nova-backend alembic downgrade -1`
2. **Container Rollback**: Re-tag and deploy previous image tag (`nova-ai-backend:v0.9.0`).
3. **Data Protection**: Restore latest database snapshot from `/var/backups/nova-ai/`.
