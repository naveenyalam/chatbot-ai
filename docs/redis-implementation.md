# NOVA AI — Redis Integration & Architecture Documentation

This document describes the design, configuration, features, testing, and operation of the Redis integration in NOVA AI.

---

## 1. Architecture Overview

NOVA AI utilizes a centralized, asynchronous helper class called `RedisService` (`backend/app/services/redis_service.py`) built on top of `redis.asyncio`. 

```
+-----------------------------------------------------------+
|                      FastAPI Engine                       |
+-----------------------------+-----------------------------+
                              |
       Lifespan Startup       |       Lifespan Shutdown
       ----------------->     |       ----------------->
                              v
+-----------------------------+-----------------------------+
|                        RedisService                       |
+-----------------------------+-----------------------------+
                              |
                 Uses ConnectionPool (Async)
                              |
                              v
+-----------------------------+-----------------------------+
|                 redis.asyncio client connection           |
+-----------------------------+-----------------------------+
                              |
       +----------------------+----------------------+
       |                      |                      |
       v                      v                      v
+--------------+      +--------------+      +--------------+
|   Caching    |      |  Rate Limit  |      |   Locks &    |
|   Services   |      |  Middleware  |      | Idempotency  |
+--------------+      +--------------+      +--------------+
```

### Key Design Aspects:
* **Connection Pooling:** `RedisService` manages a single `ConnectionPool` instance with automatic TCP socket timeout controls.
* **Non-Blocking IO:** Every database operation is performed asynchronously using `await` with zero blocking calls in the event loop.
* **Strict Namespacing:** To prevent key collisions, all stored keys are prefixed according to environment mode (`development`, `production`, `test`):
  - Cache: `nova:{ENV_MODE}:cache:{namespace}:{key}`
  - Rate limiting: `nova:{ENV_MODE}:rate_limit:{key_name}`
  - Distributed locks: `nova:{ENV_MODE}:lock:{lock_name}`
  - Idempotency: `nova:{ENV_MODE}:idempotency:{key}`

---

## 2. Configuration Parameters

The Redis connection behavior is configured entirely via environment variables defined in `.env` (or Docker Compose):

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `REDIS_URL` | `redis://localhost:6379/0` | Connection URI. If omitted, the application disables Redis and falls back to memory. |
| `REDIS_CACHE_TTL` | `300` | Default Time-To-Live (seconds) for general key caches. |
| `REDIS_TIMEOUT` | `2.0` | Maximum socket timeout (seconds) for connections and commands. |

---

## 3. Features Utilizing Redis

When Redis is active, it coordinates shared application state:
1. **API Rate Limiting:** Limits operations like `login`, `register`, `chat`, and `upload` across scaled instances.
2. **Response Cache:** Stores statistical summaries, file statuses, and metadata list results.
3. **Distributed Locks:** Ensures only one worker processes file indexing or heavy computations at a time.
4. **Idempotency Keys:** Tracks active request IDs to prevent duplicate API executions.

---

## 4. Resilience and Fallback Behavior

A key production requirement is that **the application must not crash if Redis goes offline**. 

* **Graceful Degradation:** If `RedisService` fails to connect or pings time out, operations fallback immediately to high-performance local alternatives:
  - Cache -> Thread-safe `cachetools.TTLCache` in-memory.
  - Locks -> `asyncio.Lock` wrappers.
  - Rate Limiting -> In-memory dict-based counters.
* **Auto-Recovery:** The `ping()` mechanism periodically validates connectivity. Once the Redis server recovers, the client resumes normal remote operations.

---

## 5. Health and Readiness Check

FastAPI exposes two service check endpoints that accurately reflect dependency status:

### A. Health Endpoint (`GET /health`)
Verifies that the application process is alive and lists the connection state of the internal services.
```json
{
  "status": "ok",
  "service": "nova-ai-backend",
  "services": {
    "redis": "connected",
    "database": "connected"
  }
}
```

### B. Readiness Endpoint (`GET /readiness`)
Evaluates database and Redis connectivity. In production mode, if Redis is down, it returns a `503 Service Unavailable` status code:
```json
{
  "status": "healthy",
  "database": "ok",
  "redis": "connected"
}
```

---

## 6. Local Setup and Deployment

### A. Local Setup on Windows
Since Redis is not officially supported on Windows natively, use one of the following approaches:

#### Option 1: Docker
Start a Redis container instantly:
```bash
docker run --name nova-redis -p 6379:6379 -d redis:7-alpine
```

#### Option 2: WSL2 (Ubuntu)
1. Install Redis Server:
   ```bash
   sudo apt update
   sudo apt install redis-server
   ```
2. Start the service:
   ```bash
   sudo service redis-server start
   ```

### B. Production Deployment (Docker Compose)
A production configuration is fully defined in the root `docker-compose.yml`:
```yaml
  redis:
    image: redis:7-alpine
    container_name: nova-redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```
The backend includes a dependency check (`depends_on`) that holds application boot until the Redis health check returns success.
