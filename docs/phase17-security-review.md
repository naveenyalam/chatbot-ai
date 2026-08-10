# Phase 17 Security Review — NOVA AI Platform

This document summarizes the security posture, defensive controls, sandbox structures, and vulnerability remediations verified during the Phase 17 production hardening cycle.

---

## 1. Sandbox Isolation & RestrictedPython
NOVA AI executes dynamically generated code (e.g., Python agent calculations, autonomous tools, data transformations) in a hardened python execution environment.
*   **RestrictedPython compilation**: Disallows execution of arbitrary functions or module imports.
*   **Dunder Attribute Blocking**: Prevents direct reference to `__subclasses__`, `__globals__`, and internal module loaders.
*   **Resource Bounds**: Enforces limits on CPU cycle duration, memory allocation, and total print statement output size.
*   **Inplace Variable Checks**: Safe evaluation of inplace mutation operators (`+=`, `*=`) to protect virtual thread safety.

## 2. API Authentication & Token Lifecycles
*   **JWT Handshake**: Authentication utilizes securely signed JSON Web Tokens (JWTs) using `HS256`.
*   **Token Storage**: Tokens are stored strictly via secure Client side cookie controls and checked on initial session handshakes.
*   **Rotation & Expiration**: Active sessions query the `/api/auth/me` endpoint every 30 seconds. Expired tokens are immediately trapped on the client, clean state is destroyed, and the user is redirected to `/login` to prevent stale hijacked requests.

## 3. CORS & Network Defense
*   **Strict Access-Control**: Configured selectively; headers only trust authorized local/production origins.
*   **Tenant Isolation**: Database objects (conversations, messages, files) are query-filtered using the `tenant_id` context in the FastAPI request context. One tenant cannot view or modify another's data.

## 4. RAG Query Escaping & XSS Protection
*   **Vector Query Sanitization**: Ingested files (PDFs, DOCX, TXT) undergo plain text extraction and structured parsing. Any database injection or script tag sequences are escaped prior to index storage.
*   **Markdown Sanitization**: The frontend `MarkdownRenderer` uses a custom strict parsing engine. Every block of raw text is passed through `escapeHtml` before rendering, stripping executable script components and tags, while preserving styles.

## 5. Parameter Alignments
*   **Registration Signature Fix**: Remediated the parameter order discrepancy where `registerUser(email, password, name)` was being miscalled. The workspace now registers users correctly as `(name, email, password)`.
