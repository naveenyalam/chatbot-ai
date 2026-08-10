# Runbook: Security Anomaly & Attack Mitigation

## 1. Detection
- Prometheus alert `SecurityViolationSpike` triggered.

## 2. Diagnosis
1. Inspect Nginx access logs for abusive client IP addresses: `docker compose logs nova-nginx | grep "429"`.
2. Check `nova_security_violations_total` metric breakdown.

## 3. Immediate Mitigation
1. Block offending IP address at Nginx reverse proxy level or host firewall (`ufw deny from <IP>`).
2. Rotate compromised JWT secret keys if token theft is suspected.

## 4. Recovery & Verification
1. Verify 429 / 401 error rate drops back to baseline.
