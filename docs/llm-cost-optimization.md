# NOVA AI — LLM Cost Optimization & Cost Model

This document outlines token context trimming strategies, model routing cost optimizations, and estimated operational cost projections.

---

## 1. Cost Reduction Strategies Implemented

- **Model Routing**: Routing simple classification / chat queries to cost-efficient models (`gpt-4o-mini` @ $0.15/1M input tokens) while reserving high-reasoning models for complex agent tasks.
- **History Truncation**: Truncating conversation history beyond 10 messages to prevent exponential prompt token accumulation.
- **Top-K RAG Tuning**: Limiting RAG context chunks to `top_k = 5` relevant sections.
- **Output Token Caps**: Enforcing `max_tokens = 1000` to prevent infinite model generation loops.

---

## 2. Estimated Daily & Monthly Cost Model

> [!NOTE]
> Rates based on `gpt-4o-mini` pricing ($0.15 per 1M input tokens, $0.60 per 1M output tokens). All figures are **estimates**.

| Daily Active Users | Messages / User / Day | Estimated Input Tokens | Estimated Output Tokens | Daily Cost ($) | Monthly Cost ($) |
| --- | --- | --- | --- | --- | --- |
| **100** | 10 | 1,000,000 | 250,000 | **$0.30** | **$9.00** |
| **1,000** | 10 | 10,000,000 | 2,500,000 | **$3.00** | **$90.00** |
| **10,000** | 10 | 100,000,000 | 25,000,000 | **$30.00** | **$900.00** |
| **100,000** | 10 | 1,000,000,000 | 250,000,000 | **$300.00** | **$9,000.00** |
