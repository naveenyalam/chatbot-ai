# NOVA AI — Grafana Dashboards Guide

This document details Grafana dashboard configuration (`monitoring/grafana/provisioning/dashboards/nova_dashboard.json`), panel layouts, and metric interpretation.

---

## Dashboard Panels & Metrics

1. **HTTP Request Rate & Latency**: P50, P95, and P99 request latencies by HTTP method and endpoint.
2. **LLM Calls & Provider Failovers**: Primary vs secondary provider dispatch counts, retry totals, and failover activations.
3. **Agent Runs & Tool Failures**: Agent ReAct execution runs, step timeouts, and individual tool failures (calculator, code execution).
4. **Redis & DB Operations**: Cache hit vs miss ratios, database query rates, and connection pool utilization gauges.
5. **RAG Retrieval Quality & Latency**: Average vector search latency, empty retrieval rates, and character context payload sizes.
6. **Active SSE Streams & Security Violations**: Concurrently active SSE stream connections and security anomaly violation rates.
