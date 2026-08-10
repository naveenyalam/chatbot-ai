# NOVA AI — Domain Setup & TLS / SSL Certificate Guide

This document covers DNS record configuration, Let's Encrypt automated TLS certificate issuance via Certbot, Nginx reverse proxy routing, and Server-Sent Events (SSE) streaming preservation.

---

## 1. DNS Record Configuration

Point your custom domain DNS records to the server's public IPv4 address:

| Record Type | Host | Points To / Target Value | TTL |
| --- | --- | --- | --- |
| **A** | `@` (or `yourdomain.com`) | `198.51.100.42` (Public Cloud Server IP) | 3600 |
| **A** | `www` | `198.51.100.42` | 3600 |
| **A** | `api` (Optional for separate API domain) | `198.51.100.42` | 3600 |

---

## 2. Let's Encrypt TLS Provisioning with Certbot

To obtain free, auto-renewing SSL/TLS certificates:

```bash
# 1. Update package indexes and install Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# 2. Issue SSL Certificate for your domain
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 3. Test automated certificate renewal dry-run
sudo certbot renew --dry-run
```

Certbot creates SSL certificates at:
- Certificate: `/etc/letsencrypt/live/yourdomain.com/fullchain.pem`
- Private Key: `/etc/letsencrypt/live/yourdomain.com/privkey.pem`

---

## 3. Nginx Reverse Proxy Routing Matrix

```text
HTTP (Port 80) ──── Redirect 301 ────► HTTPS (Port 443)
                                              │
                                              ├── /               → Next.js (Port 3000)
                                              ├── /api/*          → FastAPI (Port 8000)
                                              └── /api/chat/stream → FastAPI (SSE Streaming)
```

### SSE Real-Time Streaming Proxy Requirements
In `deploy/nginx/nginx.conf`, the `/api/chat/stream` location block disables response buffering to support real-time token delivery:
```nginx
location /api/chat/stream {
    proxy_pass http://backend_server;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Critical SSE Streaming Settings
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```
