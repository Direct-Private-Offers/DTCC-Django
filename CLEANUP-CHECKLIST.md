# Post-Railway Deployment Cleanup Checklist

## Background

Ash has redeployed the backend from Redis to Django, dramatically simplifying our architecture.

**What was removed:**
- ❌ Redis
- ❌ Celery
- ❌ Celery Beat
- ❌ Worker services
- ❌ Background queue runners
- ❌ Multi-service orchestration

**Current architecture:**
- ✅ Django (Python 3.11)
- ✅ PostgreSQL database
- ✅ Gunicorn WSGI server

## Cleanup Checklist

### 1. After Railway Deployment is Confirmed Working

**Verify the app runs without Redis/Celery:**

```bash
# Deploy to Railway
railway up

# Monitor logs
railway logs

# Open the app and test
railway open

# Test key endpoints
curl https://your-app.railway.app/api/health/
curl https://your-app.railway.app/api/docs/
```

### 2. Remove Redis/Celery Dependencies

Once confirmed working, remove these from `requirements.txt`:

```txt
# REMOVE THESE LINES:
celery==5.4.0
redis==5.1.1
django-redis==5.4.0
```

**Command:**
```bash
# Edit requirements.txt and remove the 3 lines above
git add requirements.txt
git commit -m "Remove Redis and Celery dependencies"
git push origin main
```

### 3. Clean Django Settings

Check `config/settings.py` for Redis/Celery configuration and remove if present:

**Look for and remove:**
```python
# Redis cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        ...
    }
}

# Celery configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
...
```

### 4. Remove Celery Files (if they exist)

Check for and remove these files:

```bash
# Check if these exist
ls celery.py 2>/dev/null
ls config/celery.py 2>/dev/null
ls apps/*/tasks.py 2>/dev/null

# If found, remove them:
git rm celery.py  # or config/celery.py
git rm apps/*/tasks.py  # if using Celery tasks
git commit -m "Remove Celery task files"
git push origin main
```

### 5. Update Django Settings Imports

Check `config/settings.py` and `config/__init__.py` for Celery imports:

**Remove if present:**
```python
from .celery import app as celery_app
__all__ = ('celery_app',)
```

### 6. Remove Redis/Celery Environment Variables

In Railway dashboard, remove these environment variables if they exist:

- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

**Note:** Railway auto-injects `REDIS_URL` if Redis addon is added. Make sure NOT to add Redis addon.

### 7. Final Verification

After all cleanup:

```bash
# Redeploy
git push origin main

# Watch deployment
railway logs --follow

# Verify everything works
railway open

# Test critical endpoints
curl https://your-app.railway.app/api/health/
curl https://your-app.railway.app/api/docs/

# Check for any Redis/Celery errors in logs
railway logs | grep -i "redis\|celery"
```

### 8. Update Documentation (Optional)

If there's any documentation about Redis/Celery setup, update or remove it.

## Benefits After Cleanup

✅ **Simpler deployment** - One less service to manage
✅ **Lower costs** - No Redis service needed
✅ **Easier scaling** - Just scale Django, not workers
✅ **Cleaner dependencies** - Fewer packages to maintain
✅ **Less complexity** - No multi-service orchestration

## Troubleshooting

### If app fails after removing dependencies:

1. **Check logs for specific errors:**
   ```bash
   railway logs
   ```

2. **Look for imports that still reference Redis/Celery:**
   ```bash
   grep -r "from celery" . --include="*.py"
   grep -r "import celery" . --include="*.py"
   grep -r "django_redis" . --include="*.py"
   grep -r "import redis" . --include="*.py"
   ```

3. **Revert changes if needed:**
   ```bash
   git revert HEAD
   git push origin main
   ```

4. **Fix the code and try again**

## Timeline

**Recommended order:**

1. ✅ **NOW:** Deploy to Railway with current dependencies (Redis/Celery still in requirements.txt)
2. ✅ **Verify:** Test thoroughly that app works on Railway
3. ⏭️ **Then:** Remove Redis/Celery dependencies and code
4. ⏭️ **Finally:** Redeploy and verify cleanup worked

This way, if something breaks, you know it's the cleanup, not the Railway deployment.

---

**Created:** 2026-01-30  
**Status:** Pending Railway deployment verification
