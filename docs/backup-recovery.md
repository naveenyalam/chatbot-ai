# NOVA AI — Backup & Disaster Recovery Guide

This document outlines backup strategies, automated snapshot scripts, cloud object storage synchronization, recovery time objectives (RTO/RPO), and disaster recovery runbooks for NOVA AI production deployments.

---

## 1. Recovery Objectives & Component Status

### Service Level Objectives
- **Recovery Point Objective (RPO)**: **< 15 minutes** (Maximum allowable data loss window).
- **Recovery Time Objective (RTO)**: **< 1 hour** (Maximum target downtime to full system restoration).

### Component Status Matrix

| Component | Target RPO | Backup Mechanism | Storage Location |
| --- | --- | --- | --- |
| **PostgreSQL Database** | 15 minutes | Automated `pg_dump` + WAL archiving | Persistent volume + AWS S3 / GCS |
| **Document Files** | 1 hour | Incremental `rsync` / `tar` snapshot | Persistent volume + AWS S3 / GCS |
| **Redis Cache** | 0 minutes (Volatile) | AOF / RDB persistence (`/data`) | Redis volume (Ephemeral; auto-rebuilt) |
| **Configuration & Secrets** | On modification | Vault / Encrypted Repository Secrets | Cloud Secret Manager / `.env` backup |

---

## 2. Automated PostgreSQL Backup & Cloud Sync

### Daily Cron Job Script (`scripts/backup_db.sh`)
```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/nova-ai"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/nova_db_${TIMESTAMP}.dump"
S3_BUCKET="s3://your-nova-ai-backups/database"

mkdir -p "$BACKUP_DIR"

# 1. Take compressed pg_dump snapshot
docker exec nova-postgres pg_dump -U postgres -F c -b -v -f "/var/lib/postgresql/data/backup_tmp.dump" nova_ai
docker cp nova-postgres:/var/lib/postgresql/data/backup_tmp.dump "$BACKUP_FILE"
docker exec nova-postgres rm -f /var/lib/postgresql/data/backup_tmp.dump

# 2. Upload to S3
if command -v aws >/dev/null 2>&1; then
    aws s3 cp "$BACKUP_FILE" "${S3_BUCKET}/nova_db_${TIMESTAMP}.dump"
    echo "Successfully synced database backup to S3."
fi

# 3. Retain last 7 days locally
find "$BACKUP_DIR" -name "*.dump" -mtime +7 -exec rm -f {} \;
```

---

## 3. Database & File Restoration Runbook

### Step 1: Restore PostgreSQL Database
```bash
# 1. Stop backend API service to freeze active connections
docker compose stop backend

# 2. Restore database from snapshot
docker cp /var/backups/nova-ai/nova_db_20260808_120000.dump nova-postgres:/tmp/restore.dump
docker exec -i nova-postgres pg_restore -U postgres -d nova_ai --clean --if-exists /tmp/restore.dump
docker exec nova-postgres rm -f /tmp/restore.dump

# 3. Run Alembic migrations to align schema
docker compose run --rm backend alembic upgrade head

# 4. Restart backend API service
docker compose start backend
```

### Step 2: Restore User Document Files
```bash
# Unpack document archive into storage volume
docker run --rm -v nova-ai_backend_storage:/volume -v /var/backups/nova-ai:/backup alpine tar -xzf /backup/nova_storage_20260808.tar.gz -C /volume
```

---

## 4. Disaster Recovery (DR) Full Restoration Protocol

In the event of total server loss:

1. **Provision Target Host**: Launch new cloud instance (Ubuntu 22.04 LTS with Docker & Docker Compose).
2. **Pull Infrastructure Code**:
   ```bash
   git clone https://github.com/your-org/chatbot-ai.git /opt/nova-ai
   cd /opt/nova-ai
   ```
3. **Inject Production Secrets**: Retrieve production `.env` from Cloud Secret Vault.
4. **Restore Storage Volume & Database Snapshot**: Pull latest dump from AWS S3 bucket and run restoration commands above.
5. **Start Production Stack**:
   ```bash
   docker compose up -d
   ```
6. **Verify Service Health**:
   ```bash
   curl -f http://localhost:8000/readiness
   ```
