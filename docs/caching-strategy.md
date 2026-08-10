# NOVA AI — Caching Strategy & Redis Namespace Isolation

This document outlines multi-tier caching, Redis key namespacing, TTL invalidation rules, and strict isolation policies.

---

## Safe Caching Candidates & Namespace Matrix

| Data Type | Redis Key Prefix | Default TTL | Invalidation Policy |
| --- | --- | --- | --- |
| **System Settings** | `nova:config:sys` | 3,600s | Invalidated on admin settings edit |
| **RAG Embedding Cache** | `nova:rag:emb:<hash>` | 86,400s | Deterministic text hash |
| **Rate Limit State** | `nova:ratelimit:<ip>` | 60s | Sliding window expiration |
| **Circuit Breaker State** | `nova:circuit:<provider>` | 60s | Resets on success or cooldown |

> [!CAUTION]
> Passwords, JWT secrets, authorization bearer tokens, and unhashed private credentials are **NEVER** cached.
