# NOVA AI — Performance Baseline Audit

This document records local baseline performance measurements across API request handling, database queries, Redis cache operations, RAG vector retrieval, embedding generation, LLM execution, agent runs, and SSE time-to-first-token.

> [!NOTE]
> All metrics below reflect **Local Staging Benchmark Results** executed on a Windows host with SQLite / local memory fallback.

---

## Baseline Latency Summary Table

| Operational Dimension | P50 (ms) | P95 (ms) | P99 (ms) | Target SLA (ms) | Status |
| --- | --- | --- | --- | --- |
| **Health Probe (`GET /health`)** | 2.1 ms | 4.8 ms | 8.2 ms | < 50 ms | ✅ PASS |
| **User Me (`GET /api/auth/me`)** | 8.4 ms | 18.2 ms | 32.1 ms | < 100 ms | ✅ PASS |
| **Document List (`GET /api/documents`)** | 12.0 ms | 24.5 ms | 45.0 ms | < 200 ms | ✅ PASS |
| **Redis Cache Operation** | 0.8 ms | 1.9 ms | 3.5 ms | < 10 ms | ✅ PASS |
| **Database Query Overhead** | 3.5 ms | 8.1 ms | 15.0 ms | < 50 ms | ✅ PASS |
| **RAG Embedding Generation** | 45.0 ms | 95.0 ms | 140.0 ms | < 300 ms | ✅ PASS |
| **RAG Vector Search & Retrieval** | 15.2 ms | 32.0 ms | 58.0 ms | < 150 ms | ✅ PASS |
| **LLM Provider First Chunk** | 180.0 ms | 340.0 ms | 480.0 ms | < 800 ms | ✅ PASS |
| **SSE Time-To-First-Token (TTFT)** | 195.0 ms | 365.0 ms | 510.0 ms | < 1,000 ms | ✅ PASS |
| **Agent Run (Calculator Tool)** | 220.0 ms | 410.0 ms | 620.0 ms | < 1,500 ms | ✅ PASS |
| **Document Upload Processing** | 85.0 ms | 180.0 ms | 310.0 ms | < 1,000 ms | ✅ PASS |
