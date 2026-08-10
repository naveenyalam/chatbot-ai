# NOVA AI — AI Quality Evaluation & Grounding Monitoring

This document describes the AI quality evaluation framework implemented in `backend/app/services/ai/quality_monitor.py`.

---

## Quality Dimensions Evaluated

1. **Grounding Score (0.0 to 1.0)**: Measures token overlap between generated AI responses and retrieved RAG context chunks.
2. **Hallucination Indicators**: Flags responses yielding grounding scores below 0.30 when retrieved context was provided.
3. **Refusal Correctness**: Ensures unanswerable queries yield standardized refusal responses (`"Information not found in retrieved documents"`) without generating false information.
4. **Prompt Injection Isolation**: Verifies vector context chunks are delimited by non-executable XML boundary tags (`<retrieved_context>`).
