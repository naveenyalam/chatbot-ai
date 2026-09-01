# NOVA AI — Redis Implementation Report

This report documents the architecture, configuration, and structural integrations implemented to activate Redis support across the NOVA AI backend.

---

## 1. Architectural Blueprint

The updated Redis activation implements a centralized, asynchronous manager (`RedisService`) that interfaces with FastAPI lifespan events, cache providers, rate limiters, distributed locks, and API endpoints.

```
                  +--------------------------------+
                  |         FastAPI Engine         |
                  +---------------+----------------+
                                  |
            Lifespan Startup      |      Lifespan Shutdown
            ---------------->     |      ----------------->
                                  v
                  +---------------+----------------+
                  |          RedisService          |
                  +---------------+----------------+
                                  |
                     Uses ConnectionPool (Async)
                                  |
                                  v
                  +---------------+----------------+
                  |     redis.asyncio client       |
                  +---------------+----------------+
                                  |
                 +----------------+----------------+
                 |                |                |
                 v                v                v
          +------------+   +------------+   +------------+
          | Caching    |   | Rate Limit |   | Locks &    |
          | & Inv.     |   | Middleware |   | Idempotency|
          +------------+   +------------+   +------------+
```

## 2. Integrated Modules & Key Scopes

All Redis operations utilize namespace-prefix and environment-mode isolation to prevent data collision between execution context types:

* **Caching**:
  - Cache namespace is prefixed: `nova:{ENV_MODE}:cache:{namespace}:{key}`
  - List Conversations caching: `nova:{settings.ENV_MODE}:user:{user_id}:conversations_list:*`
  - List Documents caching: `nova:{settings.ENV_MODE}:user:{user_id}:documents_list`
  - Document Status caching: `nova:{settings.ENV_MODE}:user:{user_id}:document_status:{document_id}`
* **Rate Limiting**:
  - Keys prefixed: `nova:{settings.ENV_MODE}:rate_limit:{key_name}`
* **Idempotency Keys**:
  - Keys prefixed: `nova:{settings.ENV_MODE}:idempotency:{key}`
* **Distributed Locks**:
  - Keys prefixed: `nova:{settings.ENV_MODE}:lock:{lock_name}`

## 3. Resilience and Failover Lifecycle

* **Automatic Local Fallback**:
  - In development environments where no active Redis instance is detected on `localhost:6379`, the system smoothly degrades to high-performance local alternatives (e.g. `TTLCache`, thread-safe local dictionaries, and asyncio Locks).
* **Connection Re-establishing**:
  - If a connection is lost, `RedisService` automatically retries to initialize connection pools.
  - Periodic pinging caches the health status for `5.0` seconds to avoid overhead and keep endpoints highly responsive.
