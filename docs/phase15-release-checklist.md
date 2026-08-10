# Production Release Checklist — Phase 15 Hardening

Use this checklist to perform live production deployments and verify post-deployment system sanity.

## Pre-Deployment Verification
- [x] Run linting analysis (`npm run lint`) — Must complete with exit code 0.
- [x] Run type checks (`npx tsc --noEmit`) — Must return zero errors.
- [x] Build the production client (`npm run build`) — Must generate static routes successfully.
- [x] Run pytest suite (`pytest backend/app/tests/`) — All 118 test cases must pass.

## Deployment Execution
- [ ] Pull latest changes on deployment target.
- [ ] Build production Docker images (`docker-compose build`).
- [ ] Run backend migrations (`docker-compose run backend alembic upgrade head`).
- [ ] Start services in daemon mode (`docker-compose up -d`).

## Post-Deployment Sanity Check
- [ ] Verify SSL certificate binds correctly and TLS handshake succeeds.
- [ ] Perform registration and login flow with a temporary account.
- [ ] Upload a test PDF document via ChatInput and verify parsing and RAG indexing progress indicators work.
- [ ] Ask a RAG-based query and verify citation overlay drawer opens.
- [ ] Toggle theme/compact settings and confirm state persists.
