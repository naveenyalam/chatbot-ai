# NOVA AI — RAG Feedback & Evaluation Pipeline

This document details RAG retrieval quality feedback signals, context precision metrics, and evaluation datasets.

---

## 1. Aggregate Feedback Signals

- **Helpful / Ungrounded Signals**: System records anonymized user satisfaction signals without storing private prompt content.
- **Empty Retrieval Rate**: Monitored via `nova_rag_empty_retrievals_total` counter.

---

## 2. Evaluation Datasets

Automated test suites in `backend/app/tests/test_rag_quality.py` use synthetic non-sensitive documents to evaluate retrieval precision and recall.
