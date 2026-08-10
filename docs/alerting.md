# NOVA AI — Prometheus Production Alerting Guide

This document outlines Prometheus alert rules (`monitoring/prometheus/alerts.yml`), severity levels, and recommended operator response actions.

---

## Alert Rules & Operator Action Matrix

| Alert Name | Severity | Trigger Condition | Operator Action |
| --- | --- | --- | --- |
| `HighAPIErrorRate` | **CRITICAL** | HTTP 5xx errors > 5% over 5m | Inspect container logs for DB connection timeouts or unhandled exceptions. Refer to `docs/runbooks/api-outage.md`. |
| `HighAPILatency` | **WARNING** | P95 latency > 1.0s over 5m | Check Redis hit rate and LLM provider latency. Refer to `docs/runbooks/high-latency.md`. |
| `DBPoolExhaustion` | **CRITICAL** | DB pool utilization > 85% | Increase `DB_POOL_SIZE` or investigate long-running unindexed queries. Refer to `docs/runbooks/database-outage.md`. |
| `RedisUnavailable` | **WARNING** | Redis errors > 5 over 2m | Verify Redis container health (`docker compose ps nova-redis`). Fallback in-memory cache is active. |
| `LLMProviderFailureSpike` | **CRITICAL** | Primary provider errors > 0.2/s | Verify primary API key validity and check LLM status page. Failover active. |
| `CircuitBreakerOpen` | **CRITICAL** | Circuit breaker state == 2 (OPEN) | Check primary provider outage status. Circuit will automatically probe after 60s cooldown. |
| `ExcessiveLLMCost` | **WARNING** | Spending rate > $50/hour | Audit active user token usage and lower per-user daily spending budget caps. Refer to `docs/runbooks/high-token-cost.md`. |
| `SecurityViolationSpike` | **CRITICAL** | Security anomalies > 0.1/s | Investigate client IP rate-limit violations and prompt injection attempts. Refer to `docs/runbooks/security-attack.md`. |
