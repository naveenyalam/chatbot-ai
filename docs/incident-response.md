# NOVA AI — Production Incident Response & Runbooks

This document provides step-by-step operational runbooks for emergency response, system outages, failover recovery, zero-downtime rollbacks, and security incidents.

---

## Runbook 1: Backend API Service Outage

### Symptoms
- Ingress returning `502 Bad Gateway` or `504 Gateway Timeout`.
- Probes `/health` or `/readiness` returning HTTP 503 or timing out.

### Triage & Resolution Steps
1. **Inspect Container Status**:
   ```bash
   docker compose ps nova-backend
   ```
2. **Examine Container Logs**:
   ```bash
   docker compose logs --tail=100 nova-backend
   ```
3. **Restart Service**:
   ```bash
   docker compose restart nova-backend
   ```
4. **Verify Liveness**:
   ```bash
   curl -i http://localhost:8000/health
   ```

---

## Runbook 2: PostgreSQL Database Outage or Pool Exhaustion

### Symptoms
- Log errors: `OperationalError: FATAL: too many connections for role` or `connection refused`.
- Backend `/readiness` probe returns `"database": "error"`.

### Triage & Resolution Steps
1. **Check Database Container**:
   ```bash
   docker compose exec postgres pg_isready -U nova_prod_user
   ```
2. **Inspect Connection Count**:
   ```bash
   docker compose exec postgres psql -U nova_prod_user -d nova_ai_production -c "SELECT count(*) FROM pg_stat_activity;"
   ```
3. **Terminate Idle Connections if Pool Exhausted**:
   ```bash
   docker compose exec postgres psql -U nova_prod_user -d nova_ai_production -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"
   ```
4. **Restart Database Container if Unresponsive**:
   ```bash
   docker compose restart postgres
   ```

---

## Runbook 3: Redis Cache & Lock Service Failure

### Symptoms
- Logs report `RedisConnectionError: Error 111 connecting to redis:6379`.
- Backend logs fallback notice `[WARNING] Redis connection failed, falling back to local memory store`.

### Triage & Resolution Steps
1. **Test Redis Ping**:
   ```bash
   docker compose exec redis redis-cli ping
   ```
2. **Restart Redis**:
   ```bash
   docker compose restart redis
   ```
3. **Flush Stale Keys if Corrupted**:
   ```bash
   docker compose exec redis redis-cli flushdb
   ```

---

## Runbook 4: Primary/Secondary LLM Provider Outage or Rate Limit

### Symptoms
- Endpoints return `503 Service Unavailable` with message `"All AI providers failed"`.
- Backend logs show repeated `CircuitBreakerOpenException` or HTTP 429 errors from primary LLM base URL.

### Triage & Resolution Steps
1. **Check Provider Status Page**: Verify OpenAI / Gemini API status.
2. **Verify Fallback Provider Key**: Ensure `FALLBACK_AI_API_KEY` is configured in `.env`.
3. **Manual Fallback Switch**: Update `AI_BASE_URL` and `AI_API_KEY` in `.env` and run `docker compose up -d nova-backend`.

---

## Runbook 5: High Latency & Request Queue Backlog

### Symptoms
- Grafana dashboard shows HTTP duration p99 > 5 seconds.
- CPU/Memory utilization spike on host.

### Triage & Resolution Steps
1. **Check Resource Utilization**:
   ```bash
   docker stats
   ```
2. **Check Async Background Worker Queue**:
   ```bash
   docker compose logs --tail=50 nova-backend | grep "job"
   ```
3. **Scale Worker Concurrency**: Increase `DB_POOL_SIZE` or scale backend instances.

---

## Runbook 6: Failed Deployment & Instant Rollback

### Symptoms
- Unhandled exceptions after deploying new container release.

### Rollback Procedure
1. **Downgrade Database Schema**:
   ```bash
   docker compose exec nova-backend alembic downgrade -1
   ```
2. **Deploy Previous Stable Image**:
   ```bash
   docker compose pull nova-backend:v0.9.0
   docker compose up -d nova-backend
   ```
3. **Verify Health**:
   ```bash
   curl -i http://localhost:8000/readiness
   ```

---

## Runbook 7: TLS / SSL Certificate Expiration

### Symptoms
- Browsers display `NET::ERR_CERT_DATE_INVALID`.

### Resolution Steps
1. **Trigger Manual Certbot Renewal**:
   ```bash
   sudo certbot renew --force-renewal
   ```
2. **Reload Nginx Configuration**:
   ```bash
   docker compose exec nova-nginx nginx -s reload
   ```

---

## Runbook 8: Disk Exhaustion / Log Overload

### Symptoms
- Disk usage 100%; database writes fail with `No space left on device`.

### Resolution Steps
1. **Identify Large Files**:
   ```bash
   df -h
   du -sh /var/lib/docker/containers/*
   ```
2. **Truncate Docker Logs**:
   ```bash
   sudo sh -c 'truncate -s 0 /var/lib/docker/containers/*/*-json.log'
   ```
3. **Clean Unused Docker Images**:
   ```bash
   docker system prune -af --volumes
   ```

---

## Runbook 9: Memory Exhaustion & OOM Kill Recovery

### Symptoms
- Container exited with status `137` (Out Of Memory kill).

### Resolution Steps
1. **Inspect Kernel OOM Events**:
   ```bash
   dmesg -T | grep -i oom
   ```
2. **Increase Container Memory Limit**: Update `deploy.resources.limits.memory` in `docker-compose.yml` (e.g. `2g`).
3. **Restart Stack**: `docker compose up -d`.

---

## Runbook 10: Security Breach / Credential Compromise Response

### Symptoms
- Unauthorized API calls or leaked JWT secret detected.

### Resolution Steps
1. **Revoke & Rotate All Secrets**:
   - Generate new `JWT_SECRET` (32+ chars).
   - Generate new `POSTGRES_PASSWORD` and `GRAFANA_ADMIN_PASSWORD`.
2. **Restart Services with New Secrets**:
   ```bash
   docker compose down
   docker compose up -d
   ```
3. **Audit User Sessions**: All existing JWT tokens are immediately invalidated upon `JWT_SECRET` rotation.
