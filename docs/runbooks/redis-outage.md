# Runbook: Redis Outage Remediation

## 1. Detection
- Prometheus alert `RedisUnavailable` triggered.
- Cache logs indicate fallback to local memory dictionary.

## 2. Diagnosis
1. Inspect Redis container logs: `docker compose logs -f nova-redis`.
2. Test Redis ping: `docker compose exec nova-redis redis-cli ping`.

## 3. Immediate Mitigation
1. Restart Redis container: `docker compose restart nova-redis`.
2. Confirm application fallback continues serving requests safely during restart.

## 4. Recovery & Verification
1. Verify Redis returns `PONG`.
2. Check `nova_redis_cache_hits_total` metric resuming growth.
