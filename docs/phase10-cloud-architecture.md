# NOVA AI — Cloud Architecture Strategy (Phase 10)

This document defines the production cloud deployment topology for NOVA AI, evaluating single-host containerized VM options against multi-node cloud managed services.

---

## 1. Primary Production Topology (Cloud VM Stack)

For predictable cost, low latency, and straightforward operations, NOVA AI deploys as an isolated Docker stack on a virtual private cloud instance (AWS EC2, DigitalOcean Droplet, GCP Compute Engine, or Azure VM).

```text
                                  Internet
                                     │
                             HTTPS / Port 443
                                     │
                          ┌──────────▼──────────┐
                          │ Nginx Gateway Proxy │
                          └──────────┬──────────┘
                                     │
                      ┌──────────────┴──────────────┐
                      ▼                             ▼
           ┌────────────────────┐        ┌────────────────────┐
           │  Next.js Frontend  │        │  FastAPI Backend   │
           │    (Port 3000)     │        │    (Port 8000)     │
           └────────────────────┘        └──────────┬─────────┘
                                                    │
                                          ┌─────────┴─────────┐
                                          ▼                   ▼
                                   ┌──────────────┐    ┌──────────────┐
                                   │  PostgreSQL  │    │    Redis     │
                                   │  + pgvector  │    │ Cache & Lock │
                                   └──────────────┘    └──────────────┘
                                          ▲                   ▲
                                          │                   │
                                   ┌──────┴───────┐    ┌──────┴───────┐
                                   │  Prometheus  │    │   Grafana    │
                                   │ (Port 9090)  │    │ (Port 3005)  │
                                   └──────────────┘    └──────────────┘
```

---

## 2. Component Responsibility Matrix

| Layer | Technology | Container Name | Production Responsibility |
| --- | --- | --- | --- |
| **Ingress & Proxy** | Nginx Alpine | `nova-nginx` | TLS termination, HTTP/2, static caching, SSE token stream pass-through |
| **Web UI** | Next.js 16 / React 19 | `nova-frontend` | SSR/Static pages, auth UI, state management, SSE streaming client |
| **API Gateway** | FastAPI / Uvicorn | `nova-backend` | Auth, chat routing, RAG vector search, agent tool execution, metrics |
| **Relational Database** | PostgreSQL 16 + pgvector | `nova-postgres` | Persistent store for users, chats, documents, and vector embeddings |
| **Cache & In-Memory Store** | Redis 7 Alpine | `nova-redis` | Shared rate limiting counters, session locks, response caching |
| **Metrics Collector** | Prometheus | `nova-prometheus` | Time-series scraper collecting request counts, durations, and error rates |
| **Visualization UI** | Grafana | `nova-grafana` | Monitoring dashboards for SLA tracking and performance metrics |

---

## 3. Alternative Managed Cloud Topology (Enterprise Mode)

When scaling beyond a single host:
- **Database**: AWS Aurora PostgreSQL / DigitalOcean Managed PostgreSQL with `pgvector`.
- **Cache**: AWS ElastiCache / Redis Enterprise Cloud (`rediss://` endpoint with TLS).
- **Application Containers**: AWS ECS Fargate, GCP Cloud Run, or Kubernetes (EKS/GKE) managing Next.js and FastAPI replicas.
