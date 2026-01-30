# Railway Quick Start Guide

## Super Simple Deployment (2 Services Only!)

### Architecture

```
Django (Python 3.11) + PostgreSQL
```

**No Redis. No Celery. No Workers. Just Django!**

---

## 🚀 Deploy in 7 Steps

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### 2. Link Your Project

```bash
cd /path/to/DTCC-Django
railway link
# Or create new: railway init
```

### 3. Add PostgreSQL

```bash
railway add --database postgresql
```

**That's it for services!** No Redis, no workers needed.

### 4. Set Core Environment Variables

```bash
# Core required variables
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
railway variables set ENVIRONMENT=production
```

### 5. Set Security Variables (Production)

```bash
# SSL and security settings
railway variables set SECURE_SSL_REDIRECT=True
railway variables set SECURE_HSTS_SECONDS=31536000
```

### 6. Set Optional Variables (As Needed)

```bash
# Frontend CORS (if you have a frontend)
railway variables set CORS_ALLOWED_ORIGINS=https://your-frontend.com

# Email service (choose one)
railway variables set OMNISEND_API_KEY=your-omnisend-key

# Payment integration
railway variables set BILLBITTS_API_KEY=your-billbitts-key

# Blockchain (if using smart contracts)
railway variables set QUICKNODE_URL=https://your-endpoint.quiknode.pro/xxxxx/
railway variables set BLOCKCHAIN_NETWORK=ARBITRUM_NOVA

# See "All Environment Variables" section below for complete list
```

### 7. Deploy!

```bash
railway up
# Or just push to GitHub (auto-deploys)
git push origin main
```

---

## 📊 Monitor

```bash
# View logs
railway logs

# Follow logs in real-time
railway logs --follow

# Open app in browser
railway open

# Check status
railway status
```

---

## ✅ Verify Deployment

```bash
# Get your Railway URL
railway open

# Test endpoints
curl https://your-app.railway.app/api/health/
curl https://your-app.railway.app/api/docs/
```

---

## 🔧 Configuration Files

- `railway.toml` - Railway config (already set up)
- `runtime.txt` - Python 3.11 (already set up)
- `requirements.txt` - Dependencies (already set up)

**You don't need to modify these!**

---

## 📝 All Environment Variables

### Required Variables

```bash
DJANGO_SETTINGS_MODULE=config.settings     # Always this value
DJANGO_SECRET_KEY=<50-char-random-string>  # Generate with: openssl rand -hex 32
DEBUG=False                                # true for dev, False for production
ALLOWED_HOSTS=.railway.app                 # Add custom domains with commas
ENVIRONMENT=production                     # or 'development' for dev mode
```

**DATABASE_URL** - Automatically provided by Railway when you add PostgreSQL

### Security Variables (Production Recommended)

```bash
SECURE_SSL_REDIRECT=True          # Redirect HTTP to HTTPS
SECURE_HSTS_SECONDS=31536000      # 1 year HSTS
CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
```

### Optional: Email Service (Choose One)

**Option 1: Omnisend (Recommended)**
```bash
OMNISEND_API_KEY=your-omnisend-api-key
```

**Option 2: SendGrid**
```bash
SENDGRID_API_KEY=SG.your-sendgrid-key
SENDGRID_FROM_EMAIL=noreply@your-domain.com
SENDGRID_FROM_NAME=DTCC STO Platform
```

### Optional: Payment Integration

```bash
BILLBITTS_API_KEY=your-billbitts-key
BILLBITTS_API_URL=https://api.billbitcoins.com
```

### Optional: Blockchain & Smart Contracts

```bash
QUICKNODE_URL=https://your-endpoint.arbitrum-nova.quiknode.pro/xxxxx/
BLOCKCHAIN_RPC_URL=https://your-endpoint.arbitrum-nova.quiknode.pro/xxxxx/
BLOCKCHAIN_NETWORK=ARBITRUM_NOVA
ISSUANCE_CONTRACT_ADDRESS=0x...
STO_CONTRACT_ADDRESS=0x...
START_BLOCK_NUMBER=0
```

### Optional: Rate Limiting

```bash
RATE_LIMIT_USER=100/min
RATE_LIMIT_ANON=20/min
```

### Optional: External Integrations

**Euroclear**
```bash
EUROCLEAR_API_BASE=https://api.euroclear.com/v1
EUROCLEAR_API_KEY=your-key
EUROCLEAR_TIMEOUT=30
```

**Clearstream**
```bash
CLEARSTREAM_PMI_BASE=https://api.clearstream.com/pmi/v1
CLEARSTREAM_PMI_KEY=your-key
CLEARSTREAM_PARTICIPANT_ID=your-id
CLEARSTREAM_TIMEOUT=30
```

**See `.env.example` for complete list of all available variables**

---

## 🎯 What Gets Deployed

Railway automatically:
1. Detects Python 3.11 from `runtime.txt`
2. Installs dependencies from `requirements.txt`
3. Runs database migrations
4. Starts Gunicorn server

**No manual steps needed!**

---

## 🔄 Updates & Redeployments

```bash
# Make code changes
git add .
git commit -m "Your changes"
git push origin main

# Railway auto-deploys on push!
# Or manual deploy:
railway up
```

---

## 🐛 Troubleshooting

### View Logs
```bash
railway logs
```

### Check Variables
```bash
railway variables
```

### Missing SECRET_KEY Error?
Use `DJANGO_SECRET_KEY` not just `SECRET_KEY`:
```bash
railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
```

### Restart Service
```bash
railway restart
```

### Connect to Database
```bash
railway run psql $DATABASE_URL
```

---

## 📚 More Info

- **Full Guide:** `DEPLOYMENT.md`
- **Environment Variables:** `.env.example`
- **Cleanup Steps:** `CLEANUP-CHECKLIST.md`
- **README:** `README.md`

---

## 💡 Pro Tips

1. **Generate secure secret key:**
   ```bash
   railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **Auto-deploy on push** - Connect GitHub repo to Railway for automatic deployments

3. **Custom domain** - Add in Railway dashboard → Settings → Domains, then:
   ```bash
   railway variables set ALLOWED_HOSTS=.railway.app,your-domain.com
   ```

4. **Environment-specific variables** - Use Railway environments for staging/production

5. **Database backups** - Railway provides automatic backups

6. **Scaling** - Adjust in Railway dashboard as needed

7. **Check all variables are set:**
   ```bash
   railway variables
   ```

---

## 🎉 Complete Setup Example

Here's a complete production setup:

```bash
# 1. Setup Railway
railway login
railway link

# 2. Add PostgreSQL
railway add --database postgresql

# 3. Set ALL required variables
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
railway variables set ENVIRONMENT=production
railway variables set SECURE_SSL_REDIRECT=True
railway variables set SECURE_HSTS_SECONDS=31536000

# 4. Optional: Add your integrations
railway variables set CORS_ALLOWED_ORIGINS=https://your-frontend.com
railway variables set OMNISEND_API_KEY=your-key
railway variables set BILLBITTS_API_KEY=your-key

# 5. Deploy
railway up

# 6. Verify
railway logs
railway open
```

---

**No Redis. No Celery. No complexity.**

Just Django + PostgreSQL on Railway with Python 3.11. ✨

---

**Last Updated:** 2026-01-30
