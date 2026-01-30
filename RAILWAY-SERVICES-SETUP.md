# Railway Multi-Service Setup

## Architecture Overview

This deployment requires **TWO Railway services**:

1. **Web Service** - Django API (Gunicorn)
2. **Listener Service** - Blockchain event listener

Both services share the same codebase and database.

---

## 🚀 Complete Setup Guide

### Step 1: Install & Login

```bash
npm install -g @railway/cli
railway login
railway link
```

### Step 2: Add PostgreSQL

```bash
railway add --database postgresql
```

### Step 3: Create Services

```bash
# Create web service (if not already created)
railway service create web

# Create listener service for blockchain events
railway service create listener
```

### Step 4: Set Environment Variables (Both Services)

These variables are shared across both services:

```bash
# Core Django Configuration
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
railway variables set ENVIRONMENT=production

# Security
railway variables set SECURE_SSL_REDIRECT=True
railway variables set SECURE_HSTS_SECONDS=31536000
railway variables set CORS_ALLOWED_ORIGINS=https://www.directprivateoffers.net

# Webhook & API Security
railway variables set WEBHOOK_SECRET=$(openssl rand -hex 32)
railway variables set API_HMAC_SECRET=$(openssl rand -hex 32)

# Email Service (Omnisend)
railway variables set OMNISEND_API_KEY=your-omnisend-api-key
railway variables set OMNISEND_API_BASE=https://api.omnisend.com/v3
railway variables set DEFAULT_FROM_EMAIL=noreply@dtcc-sto.com

# Payment Integration
railway variables set BILLBITTS_API_KEY=your-billbitts-api-key
railway variables set BILLBITTS_PRIVATE_KEY_PATH=/app/keys/billbitts.pem

# Blockchain Configuration
railway variables set QUICKNODE_URL=your-quicknode-url
railway variables set BLOCKCHAIN_RPC_URL=your-quicknode-url
railway variables set BLOCKCHAIN_NETWORK=arbitrum-nova
railway variables set START_BLOCK_NUMBER=12345678

# Smart Contract Addresses
railway variables set ISSUANCE_CONTRACT_ADDRESS=0x...
railway variables set STO_CONTRACT_ADDRESS=0x...
railway variables set DERIVATIVES_REPORTER_CONTRACT_ADDRESS=0x...
railway variables set EUROCLEAR_BRIDGE_CONTRACT_ADDRESS=0x...
railway variables set WALLET_PRIVATE_KEY=0x...

# Financial Market APIs
railway variables set EUROCLEAR_API_BASE=https://api.euroclear.com
railway variables set EUROCLEAR_API_KEY=your-euroclear-key

railway variables set CLEARSTREAM_PMI_BASE=https://api.clearstream.com
railway variables set CLEARSTREAM_PMI_KEY=your-clearstream-key

railway variables set XETRA_API_BASE=https://api.xetra.com
railway variables set XETRA_API_KEY=your-xetra-key
```

### Step 5: Deploy Web Service

```bash
railway up --service web
```

### Step 6: Configure Listener Service

The listener service needs a different start command.

In Railway dashboard:
1. Go to listener service settings
2. Set custom start command:
   ```
   python manage.py run_blockchain_listener
   ```

Or via CLI (if supported):
```bash
railway service --name listener
# Set start command in dashboard to: python manage.py run_blockchain_listener
```

### Step 7: Deploy Listener Service

```bash
railway up --service listener
```

---

## 📋 Service Details

### Web Service

**Purpose:** Handles HTTP API requests

**Start Command:**
```bash
python manage.py migrate --noinput && gunicorn config.wsgi:application
```

**Set in:** `railway.toml` (already configured)

**Endpoint:** `https://your-app.railway.app`

### Listener Service

**Purpose:** Monitors blockchain events and processes them

**Start Command:**
```bash
python manage.py run_blockchain_listener
```

**Set in:** Railway dashboard → listener service → Settings → Deploy → Start Command

**No public endpoint** (background process)

---

## 🔧 Management Commands

### Run CSD Synchronization

Manually sync with CSDs (Euroclear, Clearstream):

```bash
railway run --service web python manage.py sync_csd
```

### Run Blockchain Listener (Manual)

```bash
railway run --service web python manage.py run_blockchain_listener
```

### Database Migrations

```bash
railway run --service web python manage.py migrate
```

### Create Superuser

```bash
railway run --service web python manage.py createsuperuser
```

### Collect Static Files

```bash
railway run --service web python manage.py collectstatic --noinput
```

---

## 🔐 Complete Environment Variables

### Core Required

```bash
DJANGO_SETTINGS_MODULE=config.settings
DJANGO_SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
ALLOWED_HOSTS=.railway.app
ENVIRONMENT=production
```

### Security

```bash
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
CORS_ALLOWED_ORIGINS=https://www.directprivateoffers.net,https://directprivateoffers.net
WEBHOOK_SECRET=$(openssl rand -hex 32)
API_HMAC_SECRET=$(openssl rand -hex 32)
```

### Email (Omnisend)

```bash
OMNISEND_API_KEY=your-omnisend-api-key
OMNISEND_API_BASE=https://api.omnisend.com/v3
DEFAULT_FROM_EMAIL=noreply@dtcc-sto.com
```

### Payment (BillBitts)

```bash
BILLBITTS_API_KEY=your-billbitts-api-key
BILLBITTS_API_URL=https://api.billbitcoins.com
BILLBITTS_PRIVATE_KEY_PATH=/app/keys/billbitts.pem
```

### Blockchain

```bash
QUICKNODE_URL=your-quicknode-url
BLOCKCHAIN_RPC_URL=your-quicknode-url
BLOCKCHAIN_NETWORK=arbitrum-nova
START_BLOCK_NUMBER=12345678
ISSUANCE_CONTRACT_ADDRESS=0x...
STO_CONTRACT_ADDRESS=0x...
DERIVATIVES_REPORTER_CONTRACT_ADDRESS=0x...
EUROCLEAR_BRIDGE_CONTRACT_ADDRESS=0x...
WALLET_PRIVATE_KEY=0x...
```

### Financial APIs

```bash
EUROCLEAR_API_BASE=https://api.euroclear.com
EUROCLEAR_API_KEY=your-euroclear-key
EUROCLEAR_TIMEOUT=30

CLEARSTREAM_PMI_BASE=https://api.clearstream.com
CLEARSTREAM_PMI_KEY=your-clearstream-key
CLEARSTREAM_PARTICIPANT_ID=your-participant-id
CLEARSTREAM_TIMEOUT=30

XETRA_API_BASE=https://api.xetra.com
XETRA_API_KEY=your-xetra-key
XETRA_PARTICIPANT_ID=your-participant-id
XETRA_TIMEOUT=30
```

### Optional

```bash
RATE_LIMIT_USER=100/min
RATE_LIMIT_ANON=20/min
```

---

## 📊 Monitor Services

### View All Services

```bash
railway status
```

### View Web Service Logs

```bash
railway logs --service web
```

### View Listener Service Logs

```bash
railway logs --service listener
```

### Restart Services

```bash
railway restart --service web
railway restart --service listener
```

---

## 🔄 Deployment Workflow

### Initial Deploy

```bash
# 1. Set up database and variables (steps 1-4 above)
# 2. Deploy web service
railway up --service web

# 3. Configure listener start command in dashboard
# 4. Deploy listener service
railway up --service listener
```

### Updates

```bash
# Push to GitHub triggers auto-deploy
git push origin main

# Or manual deploy
railway up --service web
railway up --service listener
```

### Run One-Time Sync

```bash
railway run --service web python manage.py sync_csd
```

---

## 🐛 Troubleshooting

### Check Both Services Are Running

```bash
railway status
```

Should show:
- ✅ web service (running)
- ✅ listener service (running)
- ✅ postgresql (running)

### Listener Not Starting?

Check the start command is set correctly:
1. Railway dashboard
2. listener service
3. Settings → Deploy
4. Start Command: `python manage.py run_blockchain_listener`

### View Listener Logs

```bash
railway logs --service listener --follow
```

### Database Connection Issues?

Both services automatically get `DATABASE_URL` from Railway when PostgreSQL is added.

```bash
railway variables | grep DATABASE_URL
```

### Run Management Commands

Always specify the service:

```bash
railway run --service web python manage.py <command>
```

---

## 📈 Scaling

### Scale Web Service

In Railway dashboard:
- web service → Settings → Scale
- Adjust instances based on traffic

### Scale Listener Service

Generally runs as single instance (1 replica).

Multiple listeners would process same events (requires idempotency).

---

## 💡 Pro Tips

1. **Separate Logs:** Use `--service` flag to view specific service logs
2. **Environment Consistency:** Variables are shared across services automatically
3. **Health Checks:** Web service has `/api/health/` endpoint
4. **Blockchain Sync:** Run `sync_csd` periodically via cron or Railway cron
5. **Database Migrations:** Run before deploying code changes

---

## 🎯 Quick Reference

```bash
# Deploy both services
railway up --service web
railway up --service listener

# View logs
railway logs --service web
railway logs --service listener

# Run management commands
railway run --service web python manage.py sync_csd
railway run --service web python manage.py migrate

# Check status
railway status

# Restart
railway restart --service web
railway restart --service listener
```

---

**Last Updated:** 2026-01-30  
**Architecture:** Web + Listener + PostgreSQL

---

## 📅 Scheduled Management Commands

These commands should be run periodically for data synchronization:

### Sync FX Rates

Updates foreign exchange rates from market data:

```bash
railway run --service web python manage.py sync_fx_rates
```

**Recommended schedule:** Every 15 minutes during market hours

### Reconcile Positions

Reconciles positions across CSDs and internal records:

```bash
railway run --service web python manage.py reconcile_positions
```

**Recommended schedule:** Every hour or after settlements

### Sync CSD Data

Synchronizes with Euroclear, Clearstream, and other CSDs:

```bash
railway run --service web python manage.py sync_csd
```

**Recommended schedule:** Every 30 minutes or on-demand

---

## ⏰ Setting Up Cron Jobs on Railway

Railway supports cron jobs for scheduled tasks.

### Option 1: Railway Cron Service

Create a dedicated cron service:

```bash
railway service create cron
```

Configure in Railway dashboard with schedule:

**Cron Service Start Command:**
```bash
# This would run in a loop or use a cron scheduler
while true; do
  python manage.py sync_fx_rates
  python manage.py sync_csd
  python manage.py reconcile_positions
  sleep 900  # 15 minutes
done
```

### Option 2: External Cron (Recommended)

Use a service like:
- **Railway Cron** (built-in)
- **GitHub Actions** (scheduled workflows)
- **Render Cron Jobs**
- **Cronitor** or **EasyCron**

**Example GitHub Actions (.github/workflows/scheduled-tasks.yml):**

```yaml
name: Scheduled Tasks

on:
  schedule:
    # Sync FX rates every 15 minutes
    - cron: '*/15 * * * *'
    # Reconcile positions every hour
    - cron: '0 * * * *'
    # Sync CSD daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  sync-fx-rates:
    runs-on: ubuntu-latest
    steps:
      - name: Sync FX Rates
        run: |
          railway run --service web python manage.py sync_fx_rates
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  reconcile-positions:
    runs-on: ubuntu-latest
    steps:
      - name: Reconcile Positions
        run: |
          railway run --service web python manage.py reconcile_positions
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  sync-csd:
    runs-on: ubuntu-latest
    steps:
      - name: Sync CSD
        run: |
          railway run --service web python manage.py sync_csd
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Option 3: Django Celery Beat (if using Celery)

If you re-enable Celery, use Celery Beat for scheduling:

```python
# celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-fx-rates': {
        'task': 'apps.fx.tasks.sync_fx_rates',
        'schedule': crontab(minute='*/15'),
    },
    'reconcile-positions': {
        'task': 'apps.trading.tasks.reconcile_positions',
        'schedule': crontab(minute=0),  # Every hour
    },
    'sync-csd': {
        'task': 'apps.csd.tasks.sync_csd',
        'schedule': crontab(minute='*/30'),
    },
}
```

---

## 📋 Complete Management Commands Reference

### Data Synchronization

```bash
# Sync foreign exchange rates
railway run --service web python manage.py sync_fx_rates

# Sync CSD data (Euroclear, Clearstream)
railway run --service web python manage.py sync_csd

# Reconcile positions
railway run --service web python manage.py reconcile_positions
```

### Blockchain

```bash
# Run blockchain event listener (continuous)
python manage.py run_blockchain_listener
# Note: This runs as a service, not a one-time command
```

### Database

```bash
# Run migrations
railway run --service web python manage.py migrate

# Create migrations
railway run --service web python manage.py makemigrations

# Create superuser
railway run --service web python manage.py createsuperuser
```

### Django Admin

```bash
# Collect static files
railway run --service web python manage.py collectstatic --noinput

# Check deployment
railway run --service web python manage.py check --deploy

# Show migrations
railway run --service web python manage.py showmigrations
```

### Custom Commands

```bash
# Generic format
railway run --service web python manage.py <command_name> [options]
```

---

## 🔄 Recommended Task Schedule

### Real-Time (Services)

- **Web Service:** Always running (handles API requests)
- **Listener Service:** Always running (monitors blockchain events)

### Every 15 Minutes

- `sync_fx_rates` - FX rate updates

### Every 30 Minutes

- `sync_csd` - CSD data synchronization

### Every Hour

- `reconcile_positions` - Position reconciliation

### Daily

- Database backups (Railway automatic)
- Log rotation
- Health checks

### Weekly

- Full data reconciliation
- Performance monitoring

---

## 🎯 Production Task Runner Script

Create `railway-tasks.sh`:

```bash
#!/bin/bash

# Railway Production Task Runner
# Run periodic tasks on Railway

echo "Starting scheduled tasks..."

# Sync FX Rates (every 15 min)
echo "→ Syncing FX rates..."
railway run --service web python manage.py sync_fx_rates

# Sync CSD (every 30 min)
echo "→ Syncing CSD data..."
railway run --service web python manage.py sync_csd

# Reconcile Positions (every hour)
echo "→ Reconciling positions..."
railway run --service web python manage.py reconcile_positions

echo "✓ All tasks completed"
```

Make executable and run:

```bash
chmod +x railway-tasks.sh
./railway-tasks.sh
```

---

**Updated:** 2026-01-30  
**New Commands:** sync_fx_rates, reconcile_positions
