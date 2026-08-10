# NOVA AI — Frontend Production Deployment Guide

This document covers production build configuration, client environment variable handling, reverse proxy routing, and client security boundaries for the Next.js frontend application.

---

## 1. Environment Variable Architecture

In Next.js, environment variables prefixed with `NEXT_PUBLIC_` are embedded into the client-side JavaScript bundle during the build phase (`npm run build` or `docker build`).

### Configuration Parameters

| Variable | Scope | Purpose | Default / Production Value |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Client & Build | Base API URL pointing to FastAPI backend or proxy gateway | Empty in same-origin proxy setup (e.g. `""`), or `https://api.yourdomain.com` |
| `NODE_ENV` | Server Runner | Execution mode for Next.js runtime | `production` |
| `PORT` | Container | Internal container listening port | `3000` |

> [!CAUTION]
> Never store sensitive credentials (e.g., `AI_API_KEY`, `JWT_SECRET`, database passwords) in variables starting with `NEXT_PUBLIC_`. Non-prefixed variables are strictly isolated to server-side code and are never exposed to web browser clients.

---

## 2. Standalone Container Builds

The root `Dockerfile` compiles the Next.js application into a production-optimized container using a 3-stage multi-stage build (`deps` -> `builder` -> `runner`):

1. **User Isolation**: Runs under a dedicated system user (`nextjs:1001`, `gid=1001`).
2. **Asset Optimization**: Generates optimized static HTML/CSS pages and JS chunk bundles under `.next/static`.
3. **Container Build Args**:
   ```dockerfile
   ARG NEXT_PUBLIC_API_URL=http://localhost:8000
   ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
   ```

---

## 3. Reverse Proxy & SSE Streaming Integration

When deployed behind Nginx:
- Web browser clients navigate to `https://yourdomain.com/`.
- Frontend API calls to `/api/...` are routed through Nginx directly to `http://backend:8000/api/...`.
- SSE token streams (`/api/chat/stream`) utilize unbuffered HTTP connections (`proxy_buffering off`), enabling real-time character-by-character streaming without network chunk delays.

---

## 4. Production Build Verification

To test Next.js compilation locally prior to container deployment:

```bash
# 1. Type check
npx tsc --noEmit

# 2. Production build
npm run build

# 3. Start local production server
npm start
```
