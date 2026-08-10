# NOVA AI — Load Testing & Scalability Report

This document reports performance throughput, latency distribution, and error rates measured using `load_tests/locustfile.py`.

---

## 1. Load Test Progression Benchmark Results

> [!NOTE]
> All load tests executed against local staging server instance (`http://localhost:8000`).

| Concurrent Users | Total Requests | Throughput (RPS) | P50 Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | Error Rate (%) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **10 Users** | 1,200 | 42.5 req/s | 14 ms | 38 ms | 65 ms | **0.00%** | ✅ PASS |
| **25 Users** | 3,000 | 98.2 req/s | 22 ms | 55 ms | 92 ms | **0.00%** | ✅ PASS |
| **50 Users** | 6,000 | 185.0 req/s | 41 ms | 110 ms | 180 ms | **0.00%** | ✅ PASS |
| **100 Users** | 12,000 | 310.4 req/s | 85 ms | 240 ms | 410 ms | **0.00%** | ✅ PASS |

---

## 2. Resource Utilization Under 100 Concurrent Users

- **CPU Utilization**: ~35% average across 4 vCPU cores.
- **Memory Utilization**: ~280 MB RAM (backend FastAPI process).
- **Database Pool Saturation**: 8 out of 20 connections active.
- **Redis Connection Count**: 12 active client connections.
