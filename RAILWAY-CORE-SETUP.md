# Railway Core Setup Guide

## Minimal Production Deployment

This is the **absolute minimum** needed to deploy to Railway. Additional configuration can be added later.

---

## Prerequisites

- GitHub account with this repository
- Railway account (https://railway.app)
- Node.js installed (for Railway CLI)

---

## Core Setup Commands

Copy and paste these commands in order:

### 1. Install & Login

```bash
npm install -g @railway/cli
railway login
```

### 2. Link Project

```bash
cd /path/to/DTCC-Django
railway link
```

### 3. Add Database

```bash
railway add --database postgresql
```

### 4. Set Required Environment Variables

```bash
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
```

### 5. Deploy

```bash
railway up --service web
```

---

## That's It! 🎉

Your Django app is now deployed on Railway.

### Verify Deployment

```bash
# View logs
railway logs

# Open in browser
railway open

# Test API
curl $(railway status --json | jq -r '.url')/api/health/
```

---

## What Just Happened?

1. **PostgreSQL** - Railway created a database and injected `DATABASE_URL`
2. **SECRET_KEY** - Generated a secure 64-character random key
3. **Django** - Configured to run in production mode
4. **Web Service** - Deployed your Django app with Gunicorn

---

## Optional: Add More Variables Later

After core deployment works, you can add:

### Security (Recommended)

```bash
railway variables set ENVIRONMENT=production
railway variables set SECURE_SSL_REDIRECT=True
railway variables set SECURE_HSTS_SECONDS=31536000
```

### Frontend CORS

```bash
railway variables set CORS_ALLOWED_ORIGINS=https://your-frontend.com
```

### Email Service

```bash
railway variables set OMNISEND_API_KEY=your-key
```

### Payments

```bash
railway variables set BILLBITTS_API_KEY=your-key
```

### Blockchain

```bash
railway variables set QUICKNODE_URL=https://your-endpoint.quiknode.pro/xxxxx/
railway variables set BLOCKCHAIN_NETWORK=ARBITRUM_NOVA
```

See `RAILWAY-QUICK-START.md` or `.env.example` for complete list.

---

## Troubleshooting

### Check Variables

```bash
railway variables
```

Should show at minimum:
- `DJANGO_SETTINGS_MODULE`
- `DJANGO_SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL` (auto-added)

### View Logs

```bash
railway logs --follow
```

### Restart Service

```bash
railway restart
```

---

## Next Steps

1. ✅ Core deployment working? Great!
2. 📝 Add optional variables as needed
3. 🌐 Set up custom domain (Railway dashboard)
4. 🧹 Clean up Redis/Celery (see `CLEANUP-CHECKLIST.md`)
5. 📊 Monitor logs and performance

---

## Commands Reference Card

```bash
# Quick reference for core setup
railway login
railway link
railway add --database postgresql
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
railway up --service web
```

**Copy-paste ready!** ✨

---

**Last Updated:** 2026-01-30  
**Status:** Production-ready minimal deployment
