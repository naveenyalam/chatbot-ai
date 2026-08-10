# Runbook: API Outage Remediation

## 1. Detection
- Prometheus alert `HighAPIErrorRate` (>5% 5xx errors) triggered.
- `GET /health` or `/readiness` returning HTTP 500/503.

## 2. Diagnosis
1. Inspect container logs: `docker compose logs -f nova-backend`.
2. Check process state: `docker compose ps nova-backend`.
3. Check database connectivity: `docker compose exec nova-backend python -c "from app.db.database import engine; print(engine.connect())"`.

## 3. Immediate Mitigation
1. Restart backend container: `docker compose restart nova-backend`.
2. Scale backend instances if overloaded: `docker compose up -d --scale nova-backend=2`.

## 4. Recovery & Verification
1. Send test request: `curl http://localhost:8000/health`.
2. Confirm HTTP status code returns 200 `{"status": "healthy"}`.
