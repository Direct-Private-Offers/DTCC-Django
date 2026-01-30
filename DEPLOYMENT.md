# Deployment Guide - Railway

## Overview

This Django application is deployed on **Railway** using Python 3.11.

**Simplified Architecture:** Django + PostgreSQL only (no Redis, no Celery, no workers needed!)

## Python Version

**Required:** Python 3.11

The `runtime.txt` file specifies Python 3.11 for the deployment platform.

## Railway Configuration

### Files

- **`railway.toml`** - Railway deployment configuration
- **`runtime.txt`** - Specifies Python version (python-3.11)
- **`requirements.txt`** - Python dependencies

### Railway Setup

Railway automatically detects and deploys Django applications using Nixpacks.

#### 1. Prerequisites

- Railway account (https://railway.app)
- GitHub repository connected to Railway
- PostgreSQL database (provided by Railway)

**Note:** Redis is NO LONGER needed - the backend has been simplified to Django-only!

#### 2. Connect Repository

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project (or create new)
railway link

# Or create a new project
railway init
```

#### 3. Add PostgreSQL Database

Railway provides managed PostgreSQL:

```bash
# Add PostgreSQL database
railway add --database postgresql
```

Railway automatically injects the `DATABASE_URL` environment variable.

**No Redis needed!** The application has been simplified to use Django-only architecture.

#### 4. Configure Environment Variables

Set these in Railway dashboard or via CLI:

```bash
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set SECRET_KEY=your-secret-key-here
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
```

**Required Variables:**
- `DJANGO_SETTINGS_MODULE=config.settings`
- `SECRET_KEY` - Strong random secret key
- `DEBUG=False` (for production)
- `ALLOWED_HOSTS` - Your Railway domain (`.railway.app`)

**Automatically Provided by Railway:**
- `DATABASE_URL` - PostgreSQL connection string

**Optional Variables:**
- `CORS_ALLOWED_ORIGINS` - Allowed origins for CORS
- `OMNISEND_API_KEY` - For email service
- `BILLBITTS_API_KEY` - For payment integration
- Any other service API keys

#### 5. Deploy

Railway deploys automatically on every push to your main branch:

```bash
# Push to GitHub
git push origin main

# Or deploy manually via CLI
railway up
```

#### 6. Monitor Deployment

```bash
# View logs
railway logs

# Check service status
railway status

# Open deployed app
railway open
```

## Build Process

Railway's Nixpacks automatically:

1. Detects Python version from `runtime.txt` (3.11)
2. Installs dependencies from `requirements.txt`
3. Runs database migrations (`python manage.py migrate --noinput`)
4. Starts gunicorn server (`gunicorn config.wsgi:application`)

Configuration is defined in `railway.toml`:

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python manage.py migrate --noinput && gunicorn config.wsgi:application"
healthcheckPath = "/api/health/"
```

## Architecture Simplification

**This backend has been simplified!** Thanks to Ash's migration:

✅ **No longer needed:**
- ❌ Redis service
- ❌ Celery workers
- ❌ Celery Beat scheduler
- ❌ Background queue runners
- ❌ Multi-service orchestration

✅ **Current stack:**
- ✅ Django (Python 3.11)
- ✅ PostgreSQL database
- ✅ Gunicorn WSGI server

**Result:** Simpler deployment, lower costs, easier maintenance!

## Post-Deployment Cleanup

After Railway deployment is confirmed working, the following cleanup is recommended:

### Remove from `requirements.txt`:
```
celery==5.4.0
redis==5.1.1
django-redis==5.4.0
```

### Remove from Django settings (if present):
- Redis cache configuration
- Celery configuration
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND

### Verify removal:
```bash
# After removing Redis/Celery dependencies
railway up
railway logs  # Confirm app starts without errors
```

## Database Migrations

Migrations run automatically on each deployment via the `startCommand` in `railway.toml`.

Manual migration:

```bash
# Via Railway CLI
railway run python manage.py migrate

# Create new migrations locally
python manage.py makemigrations
git add apps/*/migrations/
git commit -m "Add migrations"
git push
```

## Static Files

For production, collect static files if needed:

```bash
railway run python manage.py collectstatic --noinput
```

## Troubleshooting

### View Logs

```bash
railway logs
```

### Connect to Database

```bash
# Get database URL
railway variables get DATABASE_URL

# Connect via psql
railway run psql $DATABASE_URL
```

### Restart Service

```bash
railway restart
```

### Environment Issues

Check all environment variables are set:

```bash
railway variables
```

## Health Check

Railway monitors the health endpoint: `/api/health/`

Configured in `railway.toml`:
- Path: `/api/health/`
- Timeout: 100 seconds
- Restart policy: ON_FAILURE
- Max retries: 10

## Custom Domain

To use a custom domain:

1. Go to Railway dashboard
2. Navigate to your service settings
3. Add custom domain
4. Update DNS records as instructed
5. Update `ALLOWED_HOSTS` environment variable to include your domain

## Scaling

Railway provides automatic scaling based on traffic. Configure in the Railway dashboard under service settings.

**Note:** With the simplified Django-only architecture, scaling is even easier - just one service to scale!

## Services & Costs

**Current deployment:**
- Django application (1 service)
- PostgreSQL database (1 service)

**Total:** 2 services (vs 4+ with Redis/Celery architecture)

- Free tier available with limitations
- Pay-as-you-go pricing for production
- Database included in platform costs
- **No Redis costs!**

## Support

- Railway Documentation: https://docs.railway.app
- Railway Community: https://discord.gg/railway
- Project Issues: Use GitHub issues for app-specific problems

---

**Last Updated:** 2026-01-30  
**Python Version:** 3.11  
**Platform:** Railway  
**Architecture:** Django + PostgreSQL (simplified!)
