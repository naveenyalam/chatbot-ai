# NOVA AI — Production Smoke Testing Guide

This document covers the automated post-deployment smoke test suite implemented in `backend/app/tests/test_production_smoke.py`.

---

## 1. Overview

The production smoke test suite verifies that core infrastructure, database connections, Redis fallback behavior, authentication workflows, CORS policies, Prometheus metrics, and Server-Sent Events (SSE) streaming endpoints are operating correctly in production-like environments.

---

## 2. Test Coverage Matrix

| Test Function | Target Endpoint / Capability | Verification Objective |
| --- | --- | --- |
| `test_smoke_health_and_liveness` | `GET /health` | Confirms Python process liveness probe returns HTTP 200 `status: ok` |
| `test_smoke_readiness_probe` | `GET /readiness` | Dependency-aware check verifying PostgreSQL and Redis connections |
| `test_smoke_ready_alias_probe` | `GET /ready` | Alias probe for Kubernetes/Load Balancer integration |
| `test_smoke_auth_workflow_and_cookies` | `POST /api/auth/register`, `/login`, `/me` | Tests registration, bcrypt password hashing, JWT issue, and HttpOnly cookie set |
| `test_smoke_unauthenticated_protected_route_rejection` | `GET /api/conversations` | Enforces 401 Unauthorized rejection for missing credentials |
| `test_smoke_cors_headers` | `OPTIONS /api/chat/stream` | Validates CORS preflight headers against allowed origin rules |
| `test_smoke_prometheus_metrics_and_label_safety` | `GET /metrics` | Confirms metrics scrapability and verifies absence of user emails or passwords |
| `test_smoke_redis_cache_fallback` | `cache_set`, `cache_get` | Tests Redis operations and verifies non-blocking local fallback when Redis is offline |
| `test_smoke_database_direct_connectivity` | `SELECT 1` | Confirms active connection pool query execution against the relational database |
| `test_smoke_sse_streaming_headers` | `POST /api/chat/stream` | Verifies `text/event-stream` response headers for real-time token streaming |

---

## 3. Running Smoke Tests

To execute the smoke test suite in a deployment pipeline:

```bash
cd backend
.\venv\Scripts\python -m pytest app/tests/test_production_smoke.py -v
```
