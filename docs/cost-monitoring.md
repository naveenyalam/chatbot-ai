# NOVA AI — LLM Cost Monitoring & Telemetry Guide

This document details cost tracking instrumentation in Prometheus, Grafana cost dashboards, and token consumption guardrails.

---

## 1. Prometheus Cost Metrics Instrumentated

- `nova_llm_input_tokens_total{provider, model}`: Total input tokens sent to LLM providers.
- `nova_llm_output_tokens_total{provider, model}`: Total output tokens generated.
- `nova_llm_estimated_cost_dollars_total{provider, model}`: Running estimate of dollar expenditure.

---

## 2. Token Guardrails & Budget Controls

- **Per-User Budget Cap**: Default $5.00 daily spending limit enforced via `UsageBudget` service in `backend/app/services/budget_service.py`.
- **Token Redaction**: High-cardinality user IDs and raw prompts are excluded from Prometheus metric labels to preserve PII safety.
