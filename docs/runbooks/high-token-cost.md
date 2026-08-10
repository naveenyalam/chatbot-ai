# Runbook: High Token Cost Remediation

## 1. Detection
- Prometheus alert `ExcessiveLLMCost` (> $50/hour rate) triggered.

## 2. Diagnosis
1. Inspect Grafana panel `LLM Usage & Cost`.
2. Identify top token-consuming models or endpoints.

## 3. Immediate Mitigation
1. Lower per-user daily budget cap from $5.00 to $2.00 in `app/services/budget_service.py`.
2. Truncate conversation history to 5 messages.

## 4. Recovery & Verification
1. Verify token cost rate metric stabilizes.
