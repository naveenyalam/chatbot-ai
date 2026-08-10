# Security Architecture Guide — NOVA AI

This document details the security posture, controls, and guardrails implemented across the NOVA AI application stack.

## 1. Authentication & Session Hardening
- **Strict JWT Keys**: In production mode, JWT keys must be long, unique strings (at least 32 characters) to resist dictionary attacks. A fail-fast check prevents default placeholders.
- **Secure Cookie Settings**: Authentication utilizes secure HTTP-only cookies (`Secure`, `HttpOnly`, `SameSite=Lax`) to mitigate cross-site scripting (XSS) and request forgery (CSRF) attempts.
- **IDOR Prevention**: All endpoints retrieving, editing, or deleting documents or conversations verify that the resource's owner matches the token's authenticated subject (`user_id`).

## 2. API Defensive Architecture
- **OWASP Security Headers**: The `SecurityHeadersMiddleware` appends critical protections:
  - `X-Content-Type-Options: nosniff` (mitigates content sniffing)
  - `X-Frame-Options: DENY` (prevents clickjacking)
  - `Referrer-Policy: strict-origin-when-cross-origin` (restricts header exposure)
  - `Permissions-Policy: geolocation=(), camera=(), microphone=()` (blocks APIs)
  - `Content-Security-Policy` (controls injection vectors)
  - `Strict-Transport-Security` (enforces HTTPS)
- **CORS Constraints**: Wildcard CORS (`*`) is blocked at startup if credentials are enabled in production mode.
- **Request Payload Limitation**: Rejects JSON payloads exceeding `MAX_JSON_REQUEST_SIZE` (default 1MB) with a clean `413 Payload Too Large` error, defending against memory exhaustion attacks.

## 3. RAG & LLM Prompt Hardening
To prevent prompt injection attacks (where malicious inputs inside uploaded documents override system instructions), the system uses **Defensive Boundaries**:
- Retrieve content is strictly encapsulated inside `=== BEGIN UNTRUSTED RETRIEVED CONTENT ===` and `=== END UNTRUSTED RETRIEVED CONTENT ===` boundary tags.
- Explicit **Security Compliance Guidelines** tell the LLM to treat retrieved content as pure raw data and ignore any instructions or overrides embedded within it.

## 4. Sandboxed Code Execution
The `code_execution` tool implements a two-layered defense:
1. **Docker Sandbox (`DockerSandbox`)**: Spins up an ephemeral, containerized Alpine Linux environment with:
   - Zero network connectivity (`--network none`)
   - Hard CPU limits (`--cpus 0.5`)
   - Hard memory constraints (`-m 256m`)
   - Temporary file systems disposed of immediately after run completion.
2. **RestrictedPython Fallback (`RestrictedPythonSandbox`)**: If Docker is unavailable, executing code falls back to AST-level AST-rewriting which blocks dangerous imports, file-system IO, network access, and private/dunder class attributes (`__subclasses__`, etc.).
