# NOVA AI — Distributed Observability & Tracing Architecture

This document details OpenTelemetry-compatible tracing, correlation ID propagation (`X-Request-ID`), structured logging, and strict PII / secret redaction boundaries.

---

## 1. Tracing Architecture & Correlation IDs

Every incoming HTTP and SSE request is assigned a unique `X-Request-ID` correlation token (e.g. `nova-b94793efe191`) by FastAPI request middleware.

Tracing spans created using `app.core.tracing.trace_span()` record:
- Request handling duration (ms)
- Execution path (DB query, Redis cache lookups, LLM provider streaming, RAG vector retrieval, agent tool execution)
- Exception status and error class

---

## 2. Strict PII & Secret Redaction Policy

Tracing attributes and log outputs automatically filter and replace sensitive fields with `[REDACTED]`:
- Passwords & password hashes
- JWT access tokens & session cookies
- API keys & authorization headers
- Raw uploaded document text & private user prompt contents
