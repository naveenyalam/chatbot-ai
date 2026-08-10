# Runbook: High Latency Investigation & Mitigation

## 1. Detection
- Prometheus alert `HighAPILatency` (P95 > 1.0s) triggered.

## 2. Diagnosis
1. Check Grafana panel `RAG Retrieval Latency` vs `LLM Call Latency`.
2. Inspect slow queries in PostgreSQL logs.

## 3. Immediate Mitigation
1. Clear stale cache entries if hit rate dropped: `docker compose exec nova-redis redis-cli FLUSHDB`.
2. Adjust RAG context limit (`top_k = 3`) to reduce token prompt size.

## 4. Recovery & Verification
1. Verify P95 latency drops back under 500 ms in Grafana.
