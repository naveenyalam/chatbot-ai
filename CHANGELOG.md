# Changelog

All notable changes to the NOVA AI platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.6.0] - 2026-08-08

### Added
- **Pyrefly Analyzer Boundaries**: Added workspace-root and backend-root `pyrefly.toml` files to explicitly map python execution scopes and exclude IDE virtual/in-memory diagnostics paths.
- **Python IDE Error Cleanup & Verification Reports**: Added `docs/phase17-error-cleanup.md` detailing the diagnostics resolution.

### Changed
- **VS Code Workspace Settings**: Updated `.vscode/settings.json` to configure interpreter paths, and exclude `__pyrefly_virtual__` and cache directories.
- **Backend Test Suite Fixes**: Resolved Python namespace collision (`app` as package vs fastapi instance) and NoneType checks in `test_phase10_production.py`.

## [1.5.0] - 2026-08-08

### Added
- **Global Keyboard Operations & Hotkeys**: Integrated central keyboard shortcuts in `MainLayout.tsx` (`Ctrl+N` / `Cmd+N` for new conversations, `Ctrl+K` / `Cmd+K` for command palette, and `Esc` for modals and drawers) with a custom glassmorphic **Keyboard Shortcuts Dialog**.
- **Real-Time Network Ingestion**: Configured `ChatInput.tsx` to handle live document ingestion with backend storage (`uploadDocument`), linking uploads immediately to the active RAG selected document IDs.
- **Client-Side Fault Tolerance**: Added global React `ErrorBoundary` and Next.js root-level fallback routing (`app/error.tsx`) to capture render crashes.
- **WCAG Accessibility & UX Hardening**: Implemented screen reader aria labels (`aria-expanded`, `aria-label`), clean click-outside delegation on conversation item lists, and motion reduction options.

### Changed
- Standardized toast alerts to use custom floating context elements rather than browser-blocking dialog blocks.
- Fixed TypeScript type discrepancies on toast context helpers in header elements.

## [1.4.0] - 2026-08-08

### Added
- **Complete Frontend UI/UX Transformation**: Replaced entire visual presentation system with an enterprise-grade, minimalist, AI-native dark/light mode interface inspired by modern SaaS platforms.
- **Centered Authentication Card**: Rebuilt `/login` and `/register` into a centered, max-width 440px glass card layout with brand mark, password visibility toggle, strength meter, terms acceptance, and Google/GitHub SSO action triggers.
- **UI Component Primitives**: Added standardized `Button`, `Input`, `Badge`, and `GlassPanel` components for consistent padding, focus rings, hover elevation, and status colors.
- **Dual-Theme Design System**: Comprehensive CSS token specification (`docs/phase13-ui-design-system.md`) supporting seamless switching between `.dark` and `.light` themes.
- **UI Audit & Verification Documentation**: Added `docs/phase13-ui-audit.md` and `docs/phase13-ui-verification.md`.

### Changed
- Refined `Header`, `Sidebar`, `ChatArea`, `ChatInput`, `DocumentLibrary`, `AgentWorkspace`, `CodeWorkspace`, `DashboardOverview`, and `SettingsPanel` for contrast and keyboard accessibility.

---

## [1.3.0] - 2026-08-08

### Added
- **Distributed Observability & Tracing**: Added OpenTelemetry-compatible `trace_span` context manager (`backend/app/core/tracing.py`) with PII/secret masking.
- **Prometheus Alert Rules**: Added `monitoring/prometheus/alerts.yml` covering 8 critical operational failure scenarios.
- **AI Quality Evaluation Framework**: Added `AIQualityMonitor` (`backend/app/services/ai/quality_monitor.py`) and test suite `test_quality_monitor.py`.
- **Autonomous Recovery & Chaos Suite**: Added `test_resilience_phase13.py` testing Redis failover, LLM rate-limit backoff, and DB reconnects.
- **Operational Runbooks**: Added 7 runbooks in `docs/runbooks/` for outages, high latency, cost spikes, and security attacks.
- **Grafana Dashboard Panels**: Expanded `nova_dashboard.json` with active SSE stream and security anomaly panels.

## [1.2.0] - 2026-08-08

### Added
- **RAG Quality Evaluation Suite**: `test_rag_quality.py` for automated evaluation of precision, recall, unanswerable query refusals, and prompt-injection containment.
- **LLM Provider Resilience Suite**: `test_llm_resilience.py` for primary-to-fallback failover, rate limits (HTTP 429), timeouts, and circuit breaker tripping.
- **SSE Performance Benchmark Suite**: `test_sse_performance.py` for measuring time-to-first-token (TTFT) and disconnect handling.
- **Locust Load Testing Suite**: `load_tests/locustfile.py` simulating 10 to 100 concurrent users.
- **Token Cost & Latency Telemetry**: Added Prometheus counters (`nova_llm_input_tokens_total`, `nova_llm_estimated_cost_dollars_total`, `nova_sse_first_token_latency_seconds`).
- **Performance & Capacity Documentation**: Added 9 new performance, RAG quality, cost, agent, load testing, and capacity planning reports in `docs/`.

## [1.1.0] - 2026-08-08

### Added
- **Incident Response Runbooks**: Added `docs/incident-response.md` with 10 operational runbooks for service outages, DB pool exhaustion, Redis failover, LLM provider outage, and secret compromise.
- **Phase 11 Live Deployment Report**: Added `docs/phase11-live-deployment.md`.

## [1.0.0] - 2026-08-08

### Added
- **Production Deployment Stack**: Hardened `docker-compose.yml` with isolated `nova-network` bridge, healthchecks (`/health`, `/readiness`, `pg_isready`), and resource restart policies.
- **Nginx Reverse Proxy**: Production proxy configuration with TLS Let's Encrypt support and unbuffered Server-Sent Events (`/api/chat/stream`) token delivery.
- **Alembic Database Migration Strategy**: Automated `alembic upgrade head` execution on container startup with transactional DDL safety.
- **Multi-Tenant Isolation**: Verified database and vector embedding tenant boundaries between user sessions.
- **RestrictedPython Code Sandbox**: Enforced AST sanitization blocking system attribute inspection, network access, and process spawning in agent tools.
- **Observability**: JSON structured logging with `X-Request-ID` correlation, Prometheus metrics exporter (`/metrics`), and Grafana dashboard (`:3005`).
- **CI/CD Pipeline**: 5-stage GitHub Actions workflow (`.github/workflows/ci.yml`) covering backend tests, frontend static type checks, Docker builds, migration checks, and cloud deployment.
- **Disaster Recovery**: Automated S3 backup scripts with explicit RPO (<15 min) and RTO (<1 hour) objectives.
- **Production Smoke Test Suites**: `test_production_smoke.py` (Phase 9) and `test_phase10_production.py` (Phase 10) covering 26 automated post-deployment validation vectors.

### Security
- Sanitized `REDIS_URL` credentials in error logging to prevent password token leakage.
