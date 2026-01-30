# Railway Deployment - Complete Guide

## The Definitive Step-by-Step Deployment

This guide contains **everything** you need to deploy to Railway in production.

---

## 🎯 Prerequisites

- Railway account: https://railway.app
- Node.js installed (for Railway CLI)
- Access to all API keys and credentials

---

## 📋 Step 1: Initial Setup

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Navigate to project directory
cd /path/to/DTCC-Django

# Link to Railway project
railway link
```

---

## 💾 Step 2: Add PostgreSQL Database

```bash
railway add --database postgresql
```

✅ Railway automatically creates and injects `DATABASE_URL`

---

## 🔐 Step 3: Set Core Environment Variables

### Required Core Variables

```bash
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
railway variables set ENVIRONMENT=production
```

---

## 🛡️ Step 4: Security Settings

```bash
railway variables set SECURE_SSL_REDIRECT=True
railway variables set SECURE_HSTS_SECONDS=31536000
railway variables set CORS_ALLOWED_ORIGINS=https://www.directprivateoffers.net,https://directprivateoffers.net
railway variables set WEBHOOK_SECRET=$(openssl rand -hex 32)
railway variables set API_HMAC_SECRET=$(openssl rand -hex 32)
```

---

## 📧 Step 5: Email Service (Omnisend)

```bash
railway variables set OMNISEND_API_KEY=your-omnisend-api-key
railway variables set OMNISEND_API_BASE=https://api.omnisend.com/v3
railway variables set DEFAULT_FROM_EMAIL=noreply@dtcc-sto.com
```

---

## 💳 Step 6: Payment Integration (BillBitts)

```bash
railway variables set BILLBITTS_API_KEY=your-billbitts-api-key
railway variables set BILLBITTS_API_URL=https://api.billbitcoins.com
railway variables set BILLBITTS_PRIVATE_KEY_PATH=/app/keys/billbitts.pem
```

---

## ⛓️ Step 7: Blockchain Configuration

```bash
railway variables set QUICKNODE_URL=https://your-endpoint.arbitrum-nova.quiknode.pro/xxxxx/
railway variables set BLOCKCHAIN_RPC_URL=https://your-endpoint.arbitrum-nova.quiknode.pro/xxxxx/
railway variables set BLOCKCHAIN_NETWORK=arbitrum-nova
railway variables set START_BLOCK_NUMBER=12345678
```

### Smart Contract Addresses

```bash
railway variables set ISSUANCE_CONTRACT_ADDRESS=0x...
railway variables set STO_CONTRACT_ADDRESS=0x...
railway variables set DERIVATIVES_REPORTER_CONTRACT_ADDRESS=0x...
railway variables set EUROCLEAR_BRIDGE_CONTRACT_ADDRESS=0x...
railway variables set WALLET_PRIVATE_KEY=0x...
```

---

## 🏦 Step 8: Financial Market API Integrations

### Euroclear

```bash
railway variables set EUROCLEAR_API_BASE=https://api.euroclear.com
railway variables set EUROCLEAR_API_KEY=your-euroclear-api-key
railway variables set EUROCLEAR_TIMEOUT=30
```

### Clearstream

```bash
railway variables set CLEARSTREAM_PMI_BASE=https://api.clearstream.com
railway variables set CLEARSTREAM_PMI_KEY=your-clearstream-api-key
railway variables set CLEARSTREAM_PARTICIPANT_ID=your-participant-id
railway variables set CLEARSTREAM_TIMEOUT=30
```

### XETRA (Deutsche Börse)

```bash
railway variables set XETRA_API_BASE=https://api.xetra.com
railway variables set XETRA_API_KEY=your-xetra-api-key
railway variables set XETRA_PARTICIPANT_ID=your-participant-id
railway variables set XETRA_TIMEOUT=30
```

---

## 📊 Step 9: Optional Integrations

### Neo Bank

```bash
railway variables set NEO_BANK_API_BASE=https://api.neobank.com/v1
railway variables set NEO_BANK_API_KEY=your-neo-bank-api-key
railway variables set NEO_BANK_MERCHANT_ID=your-merchant-id
railway variables set NEO_BANK_TIMEOUT=30
```

### Rate Limiting

```bash
railway variables set RATE_LIMIT_USER=100/min
railway variables set RATE_LIMIT_ANON=20/min
```

### IPFS (Optional)

```bash
railway variables set IPFS_ENABLED=false
railway variables set IPFS_GATEWAY_URL=https://ipfs.io/ipfs/
```

---

## 🚀 Step 10: Deploy Web Service

```bash
railway up --service web
```

---

## 🔊 Step 11: Create & Deploy Listener Service

```bash
# Create listener service
railway service create listener
```

Then in Railway Dashboard:
1. Go to **listener** service
2. Settings → Deploy → Start Command
3. Set to: `python manage.py run_blockchain_listener`

Deploy:
```bash
railway up --service listener
```

---

## ✅ Step 12: Verify Deployment

```bash
# Check service status
railway status

# View web service logs
railway logs --service web

# View listener service logs
railway logs --service listener

# Open application
railway open

# Test API endpoint
curl https://your-app.railway.app/api/health/
curl https://your-app.railway.app/api/docs/
```

---

## 🔄 Step 13: Run Initial Data Sync

```bash
# Sync FX rates
railway run --service web python manage.py sync_fx_rates

# Sync CSD data
railway run --service web python manage.py sync_csd

# Reconcile positions
railway run --service web python manage.py reconcile_positions
```

---

## 📦 Complete Variable Checklist

### ✅ Core Required (Must Have)

- [ ] `DJANGO_SETTINGS_MODULE=config.settings`
- [ ] `DJANGO_SECRET_KEY` (generated)
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS=.railway.app`
- [ ] `ENVIRONMENT=production`
- [ ] `DATABASE_URL` (auto-injected by Railway)

### ✅ Security (Strongly Recommended)

- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] `SECURE_HSTS_SECONDS=31536000`
- [ ] `CORS_ALLOWED_ORIGINS`
- [ ] `WEBHOOK_SECRET` (generated)
- [ ] `API_HMAC_SECRET` (generated)

### ✅ Email Service

- [ ] `OMNISEND_API_KEY`
- [ ] `OMNISEND_API_BASE=https://api.omnisend.com/v3`
- [ ] `DEFAULT_FROM_EMAIL=noreply@dtcc-sto.com`

### ✅ Payment Integration

- [ ] `BILLBITTS_API_KEY`
- [ ] `BILLBITTS_API_URL=https://api.billbitcoins.com`
- [ ] `BILLBITTS_PRIVATE_KEY_PATH=/app/keys/billbitts.pem`

### ✅ Blockchain

- [ ] `QUICKNODE_URL`
- [ ] `BLOCKCHAIN_RPC_URL`
- [ ] `BLOCKCHAIN_NETWORK=arbitrum-nova`
- [ ] `START_BLOCK_NUMBER`
- [ ] `ISSUANCE_CONTRACT_ADDRESS`
- [ ] `STO_CONTRACT_ADDRESS`
- [ ] `DERIVATIVES_REPORTER_CONTRACT_ADDRESS`
- [ ] `EUROCLEAR_BRIDGE_CONTRACT_ADDRESS`
- [ ] `WALLET_PRIVATE_KEY`

### ✅ Financial Market APIs

- [ ] `EUROCLEAR_API_BASE=https://api.euroclear.com`
- [ ] `EUROCLEAR_API_KEY`
- [ ] `CLEARSTREAM_PMI_BASE=https://api.clearstream.com`
- [ ] `CLEARSTREAM_PMI_KEY`
- [ ] `XETRA_API_BASE=https://api.xetra.com`
- [ ] `XETRA_API_KEY`

### ⚙️ Optional

- [ ] `NEO_BANK_API_KEY`
- [ ] `RATE_LIMIT_USER=100/min`
- [ ] `RATE_LIMIT_ANON=20/min`
- [ ] `IPFS_ENABLED=false`

---

## 🎯 Copy-Paste Deployment Script

Save this as `deploy-to-railway.sh`:

```bash
#!/bin/bash

echo "🚀 DTCC Django - Railway Deployment Script"
echo "=========================================="

# Step 1: Setup
echo "Step 1: Setting up Railway..."
railway login
railway link

# Step 2: Add Database
echo "Step 2: Adding PostgreSQL..."
railway add --database postgresql

# Step 3: Core Variables
echo "Step 3: Setting core variables..."
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
railway variables set ENVIRONMENT=production

# Step 4: Security
echo "Step 4: Setting security variables..."
railway variables set SECURE_SSL_REDIRECT=True
railway variables set SECURE_HSTS_SECONDS=31536000
railway variables set WEBHOOK_SECRET=$(openssl rand -hex 32)
railway variables set API_HMAC_SECRET=$(openssl rand -hex 32)

# Step 5: Email
echo "Step 5: Email service configuration..."
echo "⚠️  Please set these manually with your actual values:"
echo "railway variables set OMNISEND_API_KEY=your-key"
echo "railway variables set OMNISEND_API_BASE=https://api.omnisend.com/v3"
echo "railway variables set DEFAULT_FROM_EMAIL=noreply@dtcc-sto.com"

# Step 6: Payment
echo "Step 6: Payment integration..."
echo "⚠️  Please set these manually with your actual values:"
echo "railway variables set BILLBITTS_API_KEY=your-key"
echo "railway variables set BILLBITTS_PRIVATE_KEY_PATH=/app/keys/billbitts.pem"

# Step 7: Blockchain
echo "Step 7: Blockchain configuration..."
echo "⚠️  Please set these manually with your actual values:"
echo "railway variables set QUICKNODE_URL=your-url"
echo "railway variables set BLOCKCHAIN_RPC_URL=your-url"
echo "railway variables set BLOCKCHAIN_NETWORK=arbitrum-nova"
echo "railway variables set START_BLOCK_NUMBER=12345678"
echo "railway variables set ISSUANCE_CONTRACT_ADDRESS=0x..."
echo "railway variables set STO_CONTRACT_ADDRESS=0x..."
echo "railway variables set DERIVATIVES_REPORTER_CONTRACT_ADDRESS=0x..."
echo "railway variables set EUROCLEAR_BRIDGE_CONTRACT_ADDRESS=0x..."
echo "railway variables set WALLET_PRIVATE_KEY=0x..."

# Step 8: Financial APIs
echo "Step 8: Financial market APIs..."
echo "⚠️  Please set these manually with your actual values:"
echo "railway variables set EUROCLEAR_API_BASE=https://api.euroclear.com"
echo "railway variables set EUROCLEAR_API_KEY=your-key"
echo "railway variables set CLEARSTREAM_PMI_BASE=https://api.clearstream.com"
echo "railway variables set CLEARSTREAM_PMI_KEY=your-key"
echo "railway variables set XETRA_API_BASE=https://api.xetra.com"
echo "railway variables set XETRA_API_KEY=your-key"

# Step 9: Deploy
echo "Step 9: Ready to deploy!"
echo "Run: railway up --service web"
echo "Then create listener service and deploy"

echo ""
echo "✅ Setup complete! Follow the manual steps above for API keys."
```

---

## 🔍 Verify All Variables

```bash
# List all configured variables
railway variables

# Should include at minimum:
# - DJANGO_SETTINGS_MODULE
# - DJANGO_SECRET_KEY
# - DEBUG
# - ALLOWED_HOSTS
# - ENVIRONMENT
# - DATABASE_URL (auto-injected)
# - All API keys and integrations
```

---

## 📋 Post-Deployment Tasks

### 1. Create Superuser

```bash
railway run --service web python manage.py createsuperuser
```

### 2. Run Initial Migrations

```bash
railway run --service web python manage.py migrate
```

### 3. Collect Static Files

```bash
railway run --service web python manage.py collectstatic --noinput
```

### 4. Initial Data Sync

```bash
railway run --service web python manage.py sync_fx_rates
railway run --service web python manage.py sync_csd
railway run --service web python manage.py reconcile_positions
```

---

## 🎯 Final Architecture

```
┌─────────────────┐
│   Railway       │
├─────────────────┤
│                 │
│  Web Service    │ ← Django API (Gunicorn)
│  (always on)    │   Port: 8000
│                 │   Health: /api/health/
├─────────────────┤
│                 │
│  Listener       │ ← Blockchain Events
│  (always on)    │   Command: run_blockchain_listener
│                 │
├─────────────────┤
│                 │
│  PostgreSQL     │ ← Database
│  (managed)      │   Auto-injected DATABASE_URL
│                 │
└─────────────────┘
```

---

## 🚨 Troubleshooting

### Deployment Fails?

```bash
railway logs --service web
```

Look for:
- Missing environment variables
- Database connection errors
- Import errors

### Listener Not Running?

Check start command in Railway dashboard:
- Service: listener
- Start Command: `python manage.py run_blockchain_listener`

### Missing Variables?

```bash
railway variables | grep -i "SECRET_KEY\|DATABASE"
```

---

## 📚 Related Documentation

- **Quick Start:** `RAILWAY-QUICK-START.md`
- **Core Setup:** `RAILWAY-CORE-SETUP.md`
- **All Variables:** `RAILWAY-PRODUCTION-VARIABLES.md`
- **Multi-Service:** `RAILWAY-SERVICES-SETUP.md`
- **Environment Template:** `.env.example`
- **Cleanup:** `CLEANUP-CHECKLIST.md`

---

## ✅ Deployment Checklist

- [ ] Railway CLI installed and logged in
- [ ] Project linked to Railway
- [ ] PostgreSQL database added
- [ ] All core variables set
- [ ] Security variables configured
- [ ] Email service configured
- [ ] Payment integration set up
- [ ] Blockchain variables configured
- [ ] Financial API keys added
- [ ] Web service deployed
- [ ] Listener service created and deployed
- [ ] Health check passes
- [ ] API documentation accessible
- [ ] Initial data sync completed
- [ ] Superuser created

---

**🎉 Your DTCC Django application is now live on Railway!**

Access it at: `https://your-app.railway.app`

API Docs: `https://your-app.railway.app/api/docs/`

---

**Last Updated:** 2026-01-30  
**Complete Deployment Guide**  
**Status:** Production Ready ✅
