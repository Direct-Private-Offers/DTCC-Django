# Deployment Configuration - IMPORTANT

## Python Version Requirement

**This project requires Python 3.11** for ecosystem compatibility.

The `.python-version` file in the project root specifies Python 3.11.

## Deployment Platforms

### ✅ Railway (RECOMMENDED)

Railway is the **recommended deployment platform** for this project because:

- ✅ Supports Python 3.11 (via Nixpacks/buildpacks)
- ✅ Full Django application support with gunicorn
- ✅ PostgreSQL and Redis integration
- ✅ Environment variable management
- ✅ Automatic deployments from GitHub

**Configuration:** `railway.toml`

**Python Version:** Automatically detected from `.python-version` file

### ⚠️ Vercel (INCOMPATIBLE - DO NOT USE)

**Vercel deployment is NOT recommended and will NOT work correctly** with this project.

**Why Vercel doesn't work:**

1. ❌ **Python 3.11 NOT supported** - Vercel only supports Python 3.12 (as of 2026)
2. ❌ **No custom Docker support** - Cannot specify custom Python version
3. ❌ **Ecosystem incompatibility** - Python 3.12 breaks compatibility with other components in our ecosystem

**Current Status of vercel.json:**

The `vercel.json` file in this repository uses the **legacy/deprecated format** that attempts to specify Python 3.11:

```json
{
  "functions": {
    "api/index.py": {
      "runtime": "python3.11",
      ...
    }
  }
}
```

This configuration:
- ❌ **Will cause build failures** on Vercel (deprecated format)
- ❌ **Cannot be fixed** while maintaining Python 3.11 requirement
- ⚠️ **Is kept for documentation purposes only**

**If you attempt to deploy to Vercel:**

You will encounter the error:
```
Build Failed
Function Runtimes must have a valid version, for example `now-php@1.0.0`.
```

**Attempted fixes that don't work:**

1. ❌ Updating to modern `@vercel/python` builder → Forces Python 3.12
2. ❌ Using legacy Node 18 runtime → Being deprecated, unreliable
3. ❌ Custom Docker containers → Not supported by Vercel
4. ❌ Specifying version in config → Ignored by Vercel

## Recommended Deployment Workflow

### 1. Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Deploy
railway up
```

### 2. Configure Environment Variables

Set these in Railway dashboard or via CLI:

```bash
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set SECRET_KEY=your-secret-key
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
```

### 3. Database & Redis

Railway provides PostgreSQL and Redis add-ons:

```bash
# Add PostgreSQL
railway add postgresql

# Add Redis
railway add redis
```

## Alternative Platforms (Python 3.11 Compatible)

If you prefer not to use Railway, these platforms also support Python 3.11:

- **Render** - Supports Python 3.11 via Docker or buildpacks
- **Fly.io** - Full Docker support, any Python version
- **Heroku** - Supports Python 3.11 via buildpacks  
- **AWS Elastic Beanstalk** - Custom Python versions via Docker
- **Google Cloud Run** - Full Docker support
- **Azure App Service** - Supports Python 3.11

## Summary

| Platform | Python 3.11 Support | Status | Recommendation |
|----------|---------------------|--------|----------------|
| Railway | ✅ Yes | Working | **USE THIS** |
| Vercel | ❌ No (3.12 only) | Incompatible | **DO NOT USE** |
| Render | ✅ Yes | Alternative | OK to use |
| Fly.io | ✅ Yes | Alternative | OK to use |

## Questions?

If you need to deploy to a platform not listed here, check that it supports:
1. Python 3.11 (not 3.12)
2. Django applications
3. PostgreSQL connectivity
4. Redis connectivity

---

**Last Updated:** 2026-01-30  
**Python Version:** 3.11 (REQUIRED)
