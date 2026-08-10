# NOVA AI — Security Anomaly Monitoring & Threat Detection

This document details security anomaly monitoring, rate-limit enforcement, prompt injection detection, and sandbox isolation tracking.

---

## Monitored Threat Vectors

1. **Authentication Anomalies**: Repeated failed login attempts trigger HTTP 429 rate-limiting.
2. **Prompt Injections**: Vector text containing injection instructions (`"Ignore previous rules"`) is isolated inside XML quotes.
3. **Sandbox Violations**: Attempts to access Python dunder attributes (`__subclasses__`) in code execution tools are blocked by RestrictedPython.
4. **Telemetry**: Increments `nova_security_violations_total{violation_type}` counter without exposing user identity.
