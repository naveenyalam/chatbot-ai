# Runbook: LLM Provider Outage & Failover Remediation

## 1. Detection
- Prometheus alert `CircuitBreakerOpen` or `LLMProviderFailureSpike` triggered.
- Primary provider returning HTTP 429 / 500 / 503 errors.

## 2. Diagnosis
1. Inspect LLM provider logs: `docker compose logs nova-backend | grep "llm-provider"`.
2. Verify if secondary fallback provider is streaming responses.

## 3. Immediate Mitigation
1. Update `.env` to rotate API key or set secondary model endpoint if primary is down long-term.
2. Restart backend: `docker compose restart nova-backend`.

## 4. Recovery & Verification
1. Verify circuit breaker cooldown (60s) resets state to HALF_OPEN.
2. Send test chat prompt to confirm full response streaming.
