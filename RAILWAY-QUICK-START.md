# Railway Quick Start Guide

## Super Simple Deployment (2 Services Only!)

### Architecture

```
Django (Python 3.11) + PostgreSQL
```

**No Redis. No Celery. No Workers. Just Django!**

---

## 🚀 Deploy in 5 Steps

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

### 4. Set Environment Variables

```bash
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
```

### 5. Deploy!

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

## 📝 Environment Variables

**Required:**
- `DJANGO_SETTINGS_MODULE` - Always `config.settings`
- `SECRET_KEY` - Strong random key
- `DEBUG` - Set to `False` for production
- `ALLOWED_HOSTS` - Your Railway domain

**Auto-Injected:**
- `DATABASE_URL` - PostgreSQL connection (Railway provides this)

**Optional:**
- `CORS_ALLOWED_ORIGINS` - If you have a frontend
- `OMNISEND_API_KEY` - Email service
- `BILLBITTS_API_KEY` - Payment integration
- Other API keys as needed

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
- **Cleanup Steps:** `CLEANUP-CHECKLIST.md`
- **README:** `README.md`

---

## 💡 Pro Tips

1. **Auto-deploy on push** - Connect GitHub repo to Railway for automatic deployments
2. **Custom domain** - Add in Railway dashboard → Settings → Domains
3. **Environment-specific variables** - Use Railway environments for staging/production
4. **Database backups** - Railway provides automatic backups
5. **Scaling** - Adjust in Railway dashboard as needed

---

## 🎉 That's It!

Two services. Five commands. Done!

**No Redis. No Celery. No complexity.**

Just Django + PostgreSQL on Railway with Python 3.11.

---

**Last Updated:** 2026-01-30
