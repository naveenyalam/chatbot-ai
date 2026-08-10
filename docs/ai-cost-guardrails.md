# NOVA AI — AI Cost Guardrails & Budget Boundaries

This document details cost enforcement boundaries, token caps, and budget exhaustion handling in `backend/app/services/budget_service.py`.

---

## Enforced Limits & Boundaries

1. **Per-Request Token Limit**: Maximum `1,000` output tokens per generation request.
2. **Per-User Daily Budget**: $5.00 daily limit per authenticated user account.
3. **Global Daily Spending Cap**: Configurable via `settings.GLOBAL_DAILY_BUDGET_DOLLARS`.
4. **Context Character Cap**: RAG context truncated at `8,000` characters.
5. **Agent Step Cap**: Maximum `10` ReAct execution steps per agent run.

When a budget limit is reached, the system returns HTTP 429 / HTTP 400 with a friendly user message (`"Daily AI usage limit reached"`).
