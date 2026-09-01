# Next.js Vercel & Domain Deployment Guide

This guide provides step-by-step instructions for deploying the **NOVA AI** Next.js frontend to **Vercel** and linking a custom domain (`https://YOUR_DOMAIN.com`).

---

## 1. Prerequisites
1. A free or pro [Vercel Account](https://vercel.com).
2. The GitHub repository containing NOVA AI pushed to your account.
3. Your live Render Backend API URL (e.g. `https://nova-ai-backend.onrender.com`).
4. (Optional) A custom domain registered with Namecheap, Cloudflare, GoDaddy, or similar.

---

## 2. Deploying to Vercel

### Step 1: Import Project
1. Log in to [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** → **Project**.
3. Import your `chatbot-ai` / `nova-ai` repository.

### Step 2: Configure Build Settings
* **Framework Preset**: Next.js
* **Root Directory**: `./` (Leave default)
* **Build Command**: `npm run build`
* **Output Directory**: `.next` (Default)

### Step 3: Configure Environment Variables
Add the following Environment Variables in the Vercel deployment modal:

| Variable Name | Environment | Value |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Production, Preview, Development | `https://YOUR_RENDER_BACKEND.onrender.com` |
| `NEXT_PUBLIC_APP_URL` | Production | `https://YOUR_DOMAIN.com` |

> [!WARNING]
> Do NOT set any backend secrets (such as `CLOUD_LLM_API_KEY`, `JWT_SECRET`, or `DATABASE_URL`) in Vercel environment variables! All `NEXT_PUBLIC_*` variables are bundled into browser JavaScript files.

### Step 4: Click Deploy
Vercel will compile the Next.js frontend and issue a default URL such as `https://nova-ai.vercel.app`.

---

## 3. Connecting a Custom Domain (`https://YOUR_DOMAIN.com`)

### Step 1: Add Domain in Vercel
1. Go to your project settings in Vercel: **Settings** → **Domains**.
2. Type `YOUR_DOMAIN.com` (replace with your actual domain name) and click **Add**.
3. Select whether to add both `YOUR_DOMAIN.com` and `www.YOUR_DOMAIN.com` (recommended).

### Step 2: Configure DNS Records
Log in to your DNS registrar (e.g., Cloudflare, Namecheap, GoDaddy) and set:

* **Apex Domain (`@`)**:
  * Type: `A`
  * Name: `@`
  * Value: `76.76.21.21` (Vercel IP)
* **Subdomain (`www`)**:
  * Type: `CNAME`
  * Name: `www`
  * Value: `cname.vercel-dns.com`

### Step 3: Verify Propagation & Update Backend CORS
1. Once DNS propagates, Vercel will automatically generate a free SSL/TLS certificate for `https://YOUR_DOMAIN.com`.
2. Update the `FRONTEND_URL` environment variable on Render:
   `FRONTEND_URL=https://YOUR_DOMAIN.com,https://www.YOUR_DOMAIN.com`
3. Redeploy the Render backend.
