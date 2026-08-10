# NOVA AI Environment Configuration Guide

This document specifies all environment variables used by NOVA AI across **Development**, **Testing**, and **Production** environments.

---

## Environment Modes (`ENV_MODE`)

| Mode | Database | Redis | Cookies | Notes |
|---|---|---|---|---|
| `development` | SQLite or PostgreSQL | Local Redis or In-memory | `SECURE_COOKIES=false` | Permissive CORS, mock LLM fallback |
| `testing` | In-memory SQLite | In-memory mock | `SECURE_COOKIES=false` | Automated unit/E2E test runs |
| `production` | PostgreSQL (`pgvector`) | Redis 7+ Cluster | `SECURE_COOKIES=true` | Strict CORS, HTTPS mandatory |

---

## Detailed Variable Reference

### 1. Application & Core
- `ENV_MODE`: Defines execution mode (`development`, `testing`, `production`). Default: `development`.
- `SECURE_COOKIES`: Set to `true` when served over HTTPS. Default: `false`.

### 2. Database (`DATABASE_URL`)
- Connection string format: `postgresql://user:pass@host:port/dbname`
- SQLite fallback format: `sqlite:///./nova_ai.db`

### 3. Redis & Caching (`REDIS_URL`)
- Connection string: `redis://host:port/db`
- `REDIS_TIMEOUT`: Timeout in seconds for Redis operations (default: `2.0`).

### 4. Security & JWT
- `JWT_SECRET`: Secret key for signing JWT tokens. **Must be at least 32 characters long in production.**
- `JWT_ALGORITHM`: Signing algorithm (default: `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiration time for access tokens (default: `60`).
- `FRONTEND_URL`: Comma-separated list of permitted CORS origins.

### 5. Rate Limiting & Usage Budgets
- `RATE_LIMIT_ENABLED`: Enforces API rate limiting (`true`/`false`).
- `RATE_LIMIT_REQUESTS`: Max requests per window (default: `60`).
- `RATE_LIMIT_WINDOW_SECONDS`: Time window in seconds (default: `60`).
- `MAX_DAILY_AI_REQUESTS`: User daily budget cap (default: `1000`).

### 6. AI Provider & Models
- `AI_API_KEY`: API key for upstream LLM provider. Leave empty to use `MockLLMProvider`.
- `AI_MODEL`: Primary target model ID (e.g., `gpt-4o-mini`).
- `AI_BASE_URL`: Provider API base endpoint (default: `https://api.openai.com/v1`).
- `LLM_CIRCUIT_FAILURE_THRESHOLD`: Trip threshold for circuit breaker (default: `5`).
- `LLM_CIRCUIT_COOLDOWN_SECONDS`: Cooldown period before probing `HALF_OPEN` state (default: `60`).

---

## Production Security Best Practices

> [!CAUTION]
> Never commit `.env` files containing live secrets to source control. Use environment injection or secret stores (e.g., GitHub Secrets, AWS Secrets Manager, Kubernetes Secrets) in CI/CD pipelines.
