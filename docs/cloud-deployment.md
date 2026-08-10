# NOVA AI — Cloud Deployment & Launch Guide

This document provides step-by-step instructions for deploying NOVA AI to cloud infrastructure (AWS EC2 / ECS, GCP Compute Engine, DigitalOcean Droplet, or Kubernetes).

---

## 1. Cloud Architecture Overview

```text
                                Internet
                                   │
                                   ▼
                         ┌───────────────────┐
                         │ Cloud TLS Ingress │
                         │ (Nginx / Certbot) │
                         └─────────┬─────────┘
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
```

---

## 2. Deployment Prerequisites

1. **Cloud Virtual Machine**: 2+ vCPU, 4GB+ RAM host running Ubuntu 22.04 LTS or Docker-compatible Linux OS.
2. **Container Engine**: Docker Engine 24.0+ and Docker Compose v2.20+.
3. **Domain Name & DNS**: Domain `A` record pointing to the public cloud Elastic IP address.
4. **Cloud Secrets**: Secure 32+ character `JWT_SECRET`, valid `AI_API_KEY`, and strong database passwords.

---

## 3. Deployment Steps

### Step 1: Clone Repository & Prepare Directory
```bash
git clone https://github.com/your-org/chatbot-ai.git /opt/nova-ai
cd /opt/nova-ai
```

### Step 2: Configure Production Environment File
Copy the environment template and set production secrets:
```bash
cp .env.example .env
nano .env
```

Set the following required production variables:
```env
ENV_MODE=production
SECURE_COOKIES=true
DATABASE_URL=postgresql://postgres:SecurePassword123!@postgres:5432/nova_ai
REDIS_URL=redis://redis:6379/0
AI_API_KEY=sk-proj-your-actual-llm-provider-api-key
JWT_SECRET=your_production_secure_secret_key_min_32_characters_long
FRONTEND_URL=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com
POSTGRES_PASSWORD=SecurePassword123!
```

### Step 3: Launch Production Container Services
```bash
docker compose up --build -d
```

### Step 4: Verify Database Migrations & Container Readiness
```bash
# Check running containers
docker compose ps

# Verify database migration head
docker exec nova-backend alembic current

# Test readiness probe
curl -f http://localhost:8000/readiness
```

### Step 5: Provision Let's Encrypt TLS Certificate
```bash
# Install Certbot
sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx

# Obtain SSL Certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 4. Operational Monitoring & Logging

- **FastAPI Process Health**: `GET /health`
- **Dependency Readiness**: `GET /readiness`
- **Prometheus Metrics**: `GET /metrics` (Scraped by Prometheus on port `9090`)
- **Grafana Dashboard**: `http://<your-server-ip>:3005` (`admin` / `admin`)

---

## 5. Troubleshooting & Health Verification

- **Container Logs**: `docker compose logs -f backend`
- **Database Connection Check**: `docker exec -it nova-postgres pg_isready -U postgres`
- **Redis Ping**: `docker exec -it nova-redis redis-cli ping`
