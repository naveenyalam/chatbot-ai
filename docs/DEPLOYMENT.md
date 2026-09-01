# NOVA AI — Production Deployment Guide

> [!IMPORTANT]
> **Recommended VPS-Free Cloud Deployment**
> NOVA AI is optimized to deploy 100% VPS-free using cloud-managed services:
> - **Frontend**: Vercel (Next.js) — See [`docs/VERCEL_DEPLOYMENT.md`](VERCEL_DEPLOYMENT.md)
> - **Backend**: Render (FastAPI) — See [`docs/RENDER_DEPLOYMENT.md`](RENDER_DEPLOYMENT.md)
> - **Database**: Neon / Supabase (Managed PostgreSQL)
> - **Cache**: Upstash Redis (Serverless TLS Redis)
> - **Cloud AI**: OpenAI / OpenRouter / Groq / Together AI
> - **Status Runbook**: See [`docs/PRODUCTION_DEPLOYMENT_STATUS.md`](PRODUCTION_DEPLOYMENT_STATUS.md)

---

## 1. Deployment Architecture Options

### Option A: Serverless / Managed Cloud (Recommended — VPS-Free)
No self-hosted servers or virtual machines required. Production runs completely managed in the cloud while local development uses Ollama (`qwen2.5:3b`) on `localhost`.

### Option B: Self-Hosted Containerized VPS (Legacy / Alternative)
For hosting on a custom Linux VM using Docker Compose:

### Option A: Standard CPU Server (Cheapest Practical)
* **Specs**: 4 vCPUs, 8GB RAM (16GB recommended for concurrent usage), 80GB SSD.
* **Provider**: Hetzner (CPX31 / CCX21), DigitalOcean, or Linode.
* **Inference Speed**: Slow (~2-5 tokens/sec on CPU for `qwen2.5:3b`).

### Option B: GPU-Accelerated Server (Recommended Production)
* **Specs**: 4 vCPUs, 16GB System RAM, 100GB SSD, 1x NVIDIA T4 (16GB VRAM) or NVIDIA A10G (24GB VRAM).
* **Provider**: AWS (g4dn.xlarge / g5.xlarge), GCP (g2-standard-4), or RunPod.
* **Inference Speed**: Fast (35+ tokens/sec on GPU).

---

## 2. Operating System Setup (Ubuntu)
Ensure the server is updated and secure:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw build-essential
```

Configure the firewall:
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

---

## 3. Docker Installation
Install the official Docker Engine and Docker Compose plugin:
```bash
# Add Docker's official GPG key
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker packages
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```

### Enable GPU acceleration (Optional for GPU servers)
If deploying on a GPU-enabled VM, install the NVIDIA Container Toolkit to pass the GPU to the Ollama container:
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart docker service
sudo systemctl restart docker
```

---

## 4. Repository Setup & Git Clone
Clone your repository to the production server:
```bash
git clone https://github.com/yourusername/chatbot-ai.git /opt/nova-ai
cd /opt/nova-ai
```

---

## 5. Environment Configuration
Copy the production environment template:
```bash
cp .env.production.example .env
```

Edit the `.env` file to provide real values:
```bash
nano .env
```

---

## 6. Secrets Generation
Generate cryptographically secure 32-character keys for `JWT_SECRET` and `SECRET_KEY`:
```bash
# Generate JWT Secret
openssl rand -hex 32

# Generate Encryption Secret
openssl rand -hex 32
```
Update these keys in the `.env` file along with a strong database password (`POSTGRES_PASSWORD`).

---

## 7. Domain & DNS Configuration
Go to your domain provider (e.g., Namecheap, Cloudflare, Route 53) and create DNS records:
* **Type A**: Host: `@`, Value: `[YOUR_VPS_PUBLIC_IP]`
* **Type A**: Host: `www`, Value: `[YOUR_VPS_PUBLIC_IP]`

---

## 8. SSL Certificate Setup (Certbot Let's Encrypt)
Run Certbot on the host machine to obtain SSL certificates:
```bash
sudo apt install certbot -y
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

This generates certificates at:
* `/etc/letsencrypt/live/yourdomain.com/fullchain.pem`
* `/etc/letsencrypt/live/yourdomain.com/privkey.pem`

Map these certificates to the Nginx container's cert volume path (`./deploy/certs`) on the host:
```bash
mkdir -p deploy/certs
sudo ln -sf /etc/letsencrypt/live/yourdomain.com/fullchain.pem deploy/certs/fullchain.pem
sudo ln -sf /etc/letsencrypt/live/yourdomain.com/privkey.pem deploy/certs/privkey.pem
```

Open `deploy/nginx/nginx.conf` and uncomment the HTTPS server block (port 443) and rewrite rules.

---

## 9. Nginx Configuration
Ensure `/opt/nova-ai/deploy/nginx/nginx.conf` has proxy buffering turned off for SSE streams:
```nginx
location /api/chat/stream {
    proxy_pass http://backend_server;
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    proxy_read_timeout 600s;
}
```

---

## 10. Docker Build & Compile
Compile Next.js static assets with the correct domain and build the service containers:
```bash
docker compose build --build-arg NEXT_PUBLIC_API_URL=https://yourdomain.com
```

---

## 11. Docker Startup
Start the services in the background:
```bash
docker compose up -d
```

Verify service statuses:
```bash
docker compose ps
```

---

## 12. Ollama Model Verification
Verify that the `ollama-pull-model` container successfully downloaded the model:
```bash
# List loaded models inside the ollama container
docker compose exec ollama ollama list
```
Expected output should list `qwen2.5:3b`.

---

## 13. Database Migrations
Migrations run automatically on backend startup. To run them manually or check migration status:
```bash
docker compose exec backend alembic current
# To upgrade schema to latest:
docker compose exec backend alembic upgrade head
```

---

## 14. Health and Readiness Verification
Check endpoint responses via `curl`:
```bash
# Liveness probe
curl -I http://localhost:8000/health

# Readiness probe (verifies DB, Redis, and Ollama)
curl -I http://localhost:8000/readiness
```

---

## 15. HTTPS and Web Interface Verification
Open your browser and navigate to `https://yourdomain.com`.
Verify:
1. Browser shows a secure lock icon (valid SSL certificate).
2. The registration and login forms work.
3. Message streaming is functional and uses `qwen2.5:3b` (verified in conversation settings).

---

## 16. Backup Procedure (PostgreSQL & Vector Store)
Create a backup cron job script `/opt/nova-ai/scripts/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/nova-ai"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -t postgres pg_dump -U postgres nova_ai > $BACKUP_DIR/nova_ai_$DATE.sql
# Retain backups for 14 days
find $BACKUP_DIR -type f -mtime +14 -name "*.sql" -delete
```
Make it executable and link to cron:
```bash
chmod +x /opt/nova-ai/scripts/backup.sh
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/nova-ai/scripts/backup.sh") | crontab -
```

### Restore Command
To restore database state from a sql dump:
```bash
docker compose exec -T postgres psql -U postgres nova_ai < /var/backups/nova-ai/nova_ai_[DATE].sql
```

---

## 17. Update Procedure
To push updates to the production stack:
```bash
git pull origin main
docker compose build --build-arg NEXT_PUBLIC_API_URL=https://yourdomain.com
docker compose up -d --remove-orphans
```

---

## 18. Rollback Procedure
If an update fails:
1. Revert to the last stable Git commit:
   ```bash
   git checkout [STABLE_COMMIT_HASH]
   ```
2. Rebuild and restart the stack:
   ```bash
   docker compose build --build-arg NEXT_PUBLIC_API_URL=https://yourdomain.com
   docker compose up -d
   ```
3. Restore database snapshot (if necessary) using the restore command above.

---

## 19. Logging and Monitoring
To tail log output of application services:
```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f nginx
```

Grafana dashboard is exposed at `https://yourdomain.com:3005` (or port 3005 directly, configure admin passwords securely).

---

## 20. Troubleshooting
* **Redis Connection Offline**: Verify that `redis` container is running and healthy: `docker compose ps redis`. Inspect logs: `docker compose logs redis`.
* **Ollama Connection Timeout**: Check GPU/CPU usage. If Ollama crashes on CPU host during model load, increase VPS swap space:
  ```bash
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  ```
* **Nginx Gateway Timeout (504)**: Ensure `proxy_read_timeout` is set to `600s` for streaming endpoints.
