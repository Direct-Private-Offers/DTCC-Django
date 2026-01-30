# DTCC Django Quick Start Guide

**Goal:** Get the Django MVP running locally with mock APIs in under 30 minutes.

---

## Prerequisites

- Python 3.11+ installed
- PostgreSQL installed (or Docker)
- Redis installed (optional but recommended)
- Git

---

## Step 1: Set Up Database (10 min)

### Option A: Local PostgreSQL

```powershell
# Install PostgreSQL (if not already installed)
winget install PostgreSQL.PostgreSQL

# Create database and user
psql -U postgres
```

```sql
CREATE DATABASE dtcc_django;
CREATE USER dtcc_user WITH PASSWORD 'dev_password_123';
GRANT ALL PRIVILEGES ON DATABASE dtcc_django TO dtcc_user;
\q
```

### Option B: Docker PostgreSQL

```powershell
docker run -d `
  --name dtcc-postgres `
  -e POSTGRES_DB=dtcc_django `
  -e POSTGRES_USER=dtcc_user `
  -e POSTGRES_PASSWORD=dev_password_123 `
  -p 5432:5432 `
  postgres:15
```

---

## Step 2: Set Up Redis (5 min) - Optional

### Option A: Local Redis

```powershell
winget install Redis.Redis
redis-server
```

### Option B: Docker Redis

```powershell
docker run -d --name dtcc-redis -p 6379:6379 redis:latest
```

### Option C: Skip Redis (for now)

Comment out Redis-dependent features in settings (cache will use in-memory fallback).

---

## Step 3: Create Virtual Environment (5 min)

```powershell
# Navigate to DTCC Django directory
cd external\dtcc-django

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# If requirements.txt doesn't exist, install core deps:
pip install django djangorestframework django-cors-headers psycopg2-binary `
    dj-database-url python-dotenv httpx celery redis drf-spectacular
```

---

## Step 4: Configure Environment (2 min)

```powershell
# Copy .env.example to .env
cp .env.example .env

# Edit .env if needed (nano, notepad, or VS Code)
code .env
```

**Minimal `.env` for local development:**

```bash
DJANGO_SECRET_KEY=dev-secret-key-local-only
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgres://dtcc_user:dev_password_123@localhost:5432/dtcc_django

# Optional (comment out if Redis not installed)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Mock API keys (already set in .env.example)
# No changes needed - uses mock mode by default
```

---

## Step 5: Run Migrations (2 min)

```powershell
# Apply database migrations
python manage.py migrate

# Create superuser (for Django admin)
python manage.py createsuperuser
# Username: admin
# Email: admin@dpo.local
# Password: admin123 (dev only)
```

---

## Step 6: Start Django Server (1 min)

```powershell
# Start development server
python manage.py runserver

# Server will start at http://localhost:8000
```

---

## Step 7: Test Healthcheck (1 min)

Open browser or use curl:

```powershell
# Browser:
# http://localhost:8000/api/health

# PowerShell:
Invoke-RestMethod -Uri http://localhost:8000/api/health | ConvertTo-Json

# Expected response:
# {
#   "status": "ok",
#   "timestamp": "2025-12-27T12:00:00Z",
#   "database": "ok",
#   "mock_mode": {
#     "euroclear": true,
#     "clearstream": true
#   },
#   "redis": "ok",
#   "version": "1.0.0"
# }
```

---

## Step 8: Test Mock API Calls (5 min)

### In Django Shell

```powershell
python manage.py shell
```

```python
# Test Euroclear mock client
from apps.euroclear.client import EuroclearClient

client = EuroclearClient()
print(f"Mock mode: {client.mock_mode}")

# Test security lookup (mock data)
details = client.get_security_details('US1234567890')
print(details)
# {'isin': 'US1234567890', 'name': 'Mock Security US12', 'currency': 'USD', 'issuer': 'Mock Issuer Corp', 'status': 'active', 'mock': True}

# Test investor validation (mock - always passes)
valid = client.validate_investor('US1234567890', '0x1234...')
print(valid)  # True

# Test tokenization (mock transaction ID)
tx_id = client.initiate_tokenization({'isin': 'US1234567890', 'amount': 100000})
print(tx_id)  # MOCK-TX-US1234567890-123456
```

---

## Step 9: Access Django Admin (Optional)

Visit: http://localhost:8000/admin

Login with superuser credentials (admin / admin123)

---

## Step 10: Test API Endpoints (Optional)

### Get JWT Token

```powershell
$body = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:8000/api/auth/token `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$token = $response.access
Write-Host "Token: $token"
```

### Call Protected Endpoint

```powershell
$headers = @{
    Authorization = "Bearer $token"
}

Invoke-RestMethod -Uri http://localhost:8000/api/issuance/ `
    -Method GET `
    -Headers $headers | ConvertTo-Json
```

---

## Troubleshooting

### Database Connection Error

```
django.db.utils.OperationalError: could not connect to server
```

**Fix:**
- Ensure PostgreSQL is running: `Get-Service postgresql*`
- Check DATABASE_URL in .env matches your PostgreSQL credentials
- Test connection: `psql -U dtcc_user -d dtcc_django`

### Redis Connection Warning (Optional)

```
ConnectionError: Error connecting to Redis
```

**Fix (if you want Redis):**
- Ensure Redis is running: `redis-cli ping` (should return `PONG`)
- Check REDIS_URL in .env

**Fix (if you don't need Redis):**
- Comment out Redis lines in .env:
  ```bash
  # REDIS_URL=redis://localhost:6379/0
  # CELERY_BROKER_URL=redis://localhost:6379/0
  ```

### Migration Errors

```
django.db.utils.ProgrammingError: relation "..." does not exist
```

**Fix:**
```powershell
# Drop and recreate database (WARNING: deletes all data)
python manage.py flush --no-input
python manage.py migrate
python manage.py createsuperuser
```

### Port Already in Use

```
Error: That port is already in use.
```

**Fix:**
```powershell
# Use different port
python manage.py runserver 8001

# Or find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Next Steps

1. ✅ **Django running locally with mock APIs**
2. 🔄 **Build first API endpoint** (contracts list)
3. 🔄 **Add unit tests** for mock clients
4. 🔄 **Deploy to Railway** (production deployment)
5. ⏳ **Apply for real API credentials** (Euroclear, Clearstream, etc.)

---

## Summary

**You now have:**
- ✅ Django REST API running locally
- ✅ PostgreSQL database connected
- ✅ Mock Euroclear/Clearstream clients working
- ✅ Healthcheck endpoint (`/api/health`)
- ✅ JWT authentication configured
- ✅ Ready to build endpoints with mock data

**Total time:** ~30 minutes

**Next:** Build your first contract endpoint or start applying for real credentials (see DTCC_CREDENTIALS_PLAN.md)
