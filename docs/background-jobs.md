# NOVA AI — Background Processing & Task Architecture

This document describes asynchronous background processing via FastAPI `BackgroundTasks` in `backend/app/services/document_service.py`.

---

## Task Execution Pipeline

1. **Document Ingestion (`process_document_in_background`)**:
   - Asynchronously extracts text pages from uploaded PDF/TXT/MD files.
   - Chunks text into 800-character segments.
   - Generates vector embeddings in batches.
   - Inserts document chunks into database with status tracking (`indexed` / `failed`).
2. **Idempotency & Timeout Safeguards**:
   - `MAX_CHUNKS_PER_DOCUMENT = 10000` chunk limit prevents memory exhaustion.
   - Transaction rollbacks (`db.rollback()`) clean up partial chunk writes upon exception.
