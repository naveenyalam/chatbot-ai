# Runbook: Database Outage Remediation

## 1. Detection
- Prometheus alert `DBPoolExhaustion` (>85% utilization) triggered.
- `GET /readiness` returns DB failure error.

## 2. Diagnosis
1. Inspect PostgreSQL container logs: `docker compose logs -f nova-db`.
2. Check active connection count: `docker compose exec nova-db psql -U nova_user -d nova_db -c "SELECT count(*) FROM pg_stat_activity;"`.

## 3. Immediate Mitigation
1. Terminate idle connection locks: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '5 minutes';`.
2. Restart DB container if non-responsive: `docker compose restart nova-db`.

## 4. Recovery & Verification
1. Run migration check: `alembic current`.
2. Verify `/readiness` returns HTTP 200.
