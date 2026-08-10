# NOVA AI — Database Performance Audit & Indexing Strategy

This document details query optimization, N+1 prevention, connection pool tuning, and index coverage across PostgreSQL / SQLAlchemy models.

---

## 1. Indexing Strategy & Index Matrix

Indexes are applied to foreign key boundaries, tenant isolation columns, and time-range query fields:

| Table | Indexed Columns | Index Purpose | Query Acceleration |
| --- | --- | --- | --- |
| `users` | `email` (UNIQUE) | Fast auth lookup during login & token validation | `SELECT * FROM users WHERE email = ?` |
| `conversations` | `user_id`, `created_at` | Composite tenant isolation & chronological user history | `SELECT * FROM conversations WHERE user_id = ? ORDER BY created_at DESC` |
| `messages` | `conversation_id`, `created_at` | Fast chat thread rendering without table scans | `SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC` |
| `documents` | `user_id` | Document ownership isolation & RAG filtering | `SELECT * FROM documents WHERE user_id = ?` |

---

## 2. Connection Pool Configuration

In `.env.production.example` and `app/core/config.py`:
- `DB_POOL_SIZE = 20` (Sufficient concurrent DB worker connections)
- `DB_MAX_OVERFLOW = 10` (Burst connection overflow headroom)
- `POOL_PRE_PING = true` (Automatic dead connection detection)
- `POOL_RECYCLE = 1800` (Recycle connections every 30 minutes to prevent stales)

---

## 3. N+1 Query Elimination

- Document list endpoints use eager join strategies for model associations.
- Chat message retrieval queries load full thread lists in single indexed SELECT statements rather than iterative ORM lazy loads.
