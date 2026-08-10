# NOVA AI — Database Migration Strategy & Alembic Runbook

This document details the database migration lifecycle, Alembic configuration, schema versioning, upgrade pipeline, and rollback safeguards for NOVA AI in production environments.

---

## 1. Migration Architecture

NOVA AI uses **Alembic** alongside **SQLAlchemy** to manage schema evolution against PostgreSQL (equipped with `pgvector`).

### Key Locations
- **Configuration File**: `backend/alembic.ini`
- **Environment Script**: `backend/db/migrations/env.py`
- **Revision Scripts**: `backend/db/migrations/versions/`

---

## 2. Production Startup Execution

In containerized production deployments (`nova-backend`), schema migrations are executed automatically prior to binding the HTTP web server.

### Startup Command
```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Safety Guarantees
1. **Idempotency**: Running `alembic upgrade head` on an already up-to-date schema is a zero-op.
2. **Transaction Isolation**: Migration scripts run inside explicit DDL transactions (`context.begin_transaction()`). If any migration step fails, the entire transaction rolls back cleanly without leaving partial schema mutations.
3. **Model Auto-Registration**: `db/migrations/env.py` imports `app.models` so all SQLAlchemy entities (`User`, `Conversation`, `Message`, `Document`, `AgentRun`, `MessageSource`) are registered under `target_metadata`.

---

## 3. Developer Migration Workflow

### Step 1: Create a Migration Revision
When changing SQLAlchemy models in `backend/app/models/`:
```bash
cd backend
.\venv\Scripts\python -m alembic revision --autogenerate -m "add_new_feature_column"
```

### Step 2: Review Generated Migration Script
Inspect the auto-generated python script in `backend/db/migrations/versions/<hash>_add_new_feature_column.py`. Verify `upgrade()` and `downgrade()` functions.

### Step 3: Test Migration Locally
```bash
# Check current migration head
.\venv\Scripts\python -m alembic current

# Upgrade to latest revision
.\venv\Scripts\python -m alembic upgrade head

# Test downgrade safety
.\venv\Scripts\python -m alembic downgrade -1

# Re-apply upgrade
.\venv\Scripts\python -m alembic upgrade head
```

---

## 4. Rollback & Disaster Recovery Safeguards

If a production deployment encounters an issue with a newly applied schema revision:

1. **Check Migration Version**:
   ```bash
   docker exec -it nova-backend alembic current
   ```
2. **Rollback 1 Revision**:
   ```bash
   docker exec -it nova-backend alembic downgrade -1
   ```
3. **Target Specific Revision**:
   ```bash
   docker exec -it nova-backend alembic downgrade <previous_revision_hash>
   ```

> [!CAUTION]
> Never execute destructive schema commands (`Base.metadata.drop_all()`) in production. Always rely on Alembic versioned migration scripts.
