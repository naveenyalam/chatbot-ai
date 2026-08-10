# NOVA AI — Cloud Provider Setup Guide (Phase 10)

This document provides provider-neutral setup instructions and details the exact cloud credentials required from developers to provision NOVA AI in cloud environments.

---

## 1. Developer-Provided Parameters Check

To complete actual cloud deployment, the following parameters and secrets must be injected into environment variables or GitHub Secrets (`.github/workflows/ci.yml`):

### Required Environment Credentials

| Parameter Name | Target Scope | Example Value | Mandatory for Cloud Deploy |
| --- | --- | --- | --- |
| `CLOUD_DEPLOY_HOST` | SSH / Infra | `198.51.100.42` or `app.yourdomain.com` | **YES** |
| `CLOUD_SSH_USER` | Server Login | `ubuntu` or `root` | **YES** |
| `CLOUD_SSH_KEY` | SSH Key Pair | `-----BEGIN OPENSSH PRIVATE KEY-----...` | **YES** |
| `AI_API_KEY` | LLM Provider | `sk-proj-prod-key...` | **YES** |
| `JWT_SECRET` | Auth Signing | `c8e9f2a1b4d3e5f7a9b2c4d6e8f1a3b5...` (32+ chars) | **YES** |
| `POSTGRES_PASSWORD` | DB Security | `ProdDbSecurePassword2026!` | **YES** |
| `GRAFANA_ADMIN_PASSWORD` | Telemetry UI | `GrafanaAdminPassword2026!` | **YES** |

---

## 2. Provider-Specific Deployment Procedures

### Option A: DigitalOcean Droplet / AWS EC2 / GCP Compute Engine
1. **Provision Instance**: Ubuntu 22.04 LTS (minimum 2 vCPU, 4GB RAM).
2. **Assign Elastic / Static IP**: Attach a permanent IPv4 address.
3. **Configure Firewall Security Group**:
   - Inbound `80` (HTTP) -> Open to 0.0.0.0/0
   - Inbound `443` (HTTPS) -> Open to 0.0.0.0/0
   - Inbound `22` (SSH) -> Restricted to admin IP
   - Inbound `3005`, `5432`, `6379`, `8000`, `9090` -> **BLOCKED** from public access
4. **Deploy Stack**:
   ```bash
   git clone https://github.com/your-org/chatbot-ai.git /opt/nova-ai
   cd /opt/nova-ai
   cp .env.production.example .env
   docker compose up --build -d
   ```

### Option B: Managed Container Platforms (Render / Railway / Fly.io)
1. **Deploy Backend Service**: Point build context to `/backend` (`backend/Dockerfile`), attach PostgreSQL + Redis add-ons, set `ENV_MODE=production`.
2. **Deploy Frontend Web Service**: Point build context to root (`Dockerfile`), set `NEXT_PUBLIC_API_URL` to backend service URL.
