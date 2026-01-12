# DTCC STO Backend API

> Production-ready Django REST Framework backend for DTCC-compliant Security Token Operations (STO) with Euroclear and Clearstream integrations.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.16-red.svg)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Proprietary-lightgrey.svg)]()

## Overview

Backend REST API for DTCC-compliant security token operations. Supports token issuance, derivatives reporting, Euroclear/Clearstream settlement sync, corporate actions, secure webhooks, and DEX/P2P flows.

Deployment: Vercel serverless functions (no Docker required).

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Security & Access Control](#security--access-control)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [API Usage Examples](#api-usage-examples)
- [Configuration](#configuration)
- [Database Management](#database-management)
- [Documentation](#documentation)
- [Development](#development)

## Features

### Core Functionality
- Security token issuance with investor validation
- Derivatives reporting (DTCC/CSA)
- Settlement management (Euroclear, Clearstream)
- Corporate actions (dividends, splits, mergers, rights)
- Clearstream PMI integration (accounts, positions)
- DEX/SWAP P2P trading and order matching
- Wallet-to-wallet transfers on-chain
- Blockchain event listener (QuickNode) and ingestion

### Security & Compliance
- JWT authentication
- Role-based access control (issuer, reporter, ops)
- Rate limiting (global and per-endpoint)
- Idempotency for POST endpoints
- Webhook HMAC with timestamp/nonce replay protection
- Request ID and session activity tracking

### Developer Experience
- OpenAPI docs (Swagger/ReDoc) with examples
- Testing guide and pytest setup
- Windows development guidance
- PostgreSQL-focused configuration

## Architecture

### Project Structure

```
backend/
├── config/              # Django settings, URLs, WSGI/ASGI configuration
├── apps/
│   ├── core/           # Core utilities (responses, idempotency, crypto, permissions, middleware)
│   ├── euroclear/      # Euroclear API client integration
│   ├── issuance/       # Token issuance endpoints
│   ├── derivatives/    # Derivatives reporting endpoints
│   ├── settlement/     # Settlement management (Euroclear)
│   ├── corporate_actions/  # Corporate actions processing
│   ├── clearstream/    # Clearstream PMI integration
│   ├── webhooks/       # Webhook handlers (Euroclear, Clearstream, Chainlink)
│   └── dex/            # DEX/SWAP P2P trading and wallet management
├── docs/               # Documentation (setup guides, API testing)
└── manage.py           # Django management script
```

## Workflow

```mermaid
flowchart LR
    User[Issuer/Reporter/Ops] --> Auth[JWTAuth]
    Auth --> Api[DRF_API_Gateway]

    Api --> IssuanceSvc[Issuance]
    Api --> DerivSvc[Derivatives]
    Api --> SettleSvc[Settlement]
    Api --> CorpSvc[Corporate_Actions]
    Api --> ClearstreamSvc[Clearstream]
    Api --> DexSvc[DEX_P2P]

    IssuanceSvc --> DB[(PostgreSQL)]
    DerivSvc --> DB
    SettleSvc --> DB
    CorpSvc --> DB
    ClearstreamSvc --> DB
    DexSvc --> DB

    subgraph Async
        Webhooks[HMAC_Webhooks] --> Tasks[Celery_Tasks]
        Tasks --> DB
    end

    CSDs[Euroclear/Clearstream] --> Webhooks
    Chain[Smart_Contracts] --> Listener[Blockchain_Listener]
    Listener --> DB
    Listener --> Api
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/token` | Obtain JWT access and refresh tokens |
| POST | `/api/auth/token/refresh` | Refresh access token |

### Documentation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/schema/` | OpenAPI schema (JSON) |
| GET | `/api/docs/` | Swagger UI |
| GET | `/api/redoc/` | ReDoc UI |

### Issuance
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| POST | `/api/issuance/` | Initiate token issuance | `issuer` |
| GET | `/api/issuance/?isin=<ISIN>` | Get security details | Authenticated |

### Derivatives
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| POST | `/api/derivatives/` | Report derivative trade (DTCC/CSA) | `reporter` |
| GET | `/api/derivatives/?uti=<UTI>` | Get derivative by UTI | Authenticated |
| GET | `/api/derivatives/?isin=<ISIN>` | Get derivative by ISIN | Authenticated |

### Settlement (Euroclear)
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| POST | `/api/settlement/` | Create settlement instruction | `issuer` |
| GET | `/api/settlement/<uuid:id>/` | Get settlement status | Authenticated |

### Corporate Actions
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| POST | `/api/corporate-actions/` | Schedule corporate action | `issuer` |
| GET | `/api/corporate-actions/` | List corporate actions (filterable) | Authenticated |

### Clearstream
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| POST | `/api/clearstream/accounts` | Link CSD account | `ops`, `issuer` |
| GET | `/api/clearstream/positions/<account>` | Get account positions | Authenticated |
| POST | `/api/clearstream/instructions` | Create instruction | `ops`, `issuer` |
| POST | `/api/clearstream/settlement` | Create Clearstream settlement | `ops`, `issuer` |
| GET | `/api/clearstream/settlement/<uuid:id>` | Get settlement status | Authenticated |

### Webhooks
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/webhooks/euroclear` | Euroclear webhook (HMAC) | HMAC only |
| POST | `/api/webhooks/clearstream` | Clearstream webhook (HMAC) | HMAC only |
| POST | `/api/webhooks/chainlink` | Chainlink oracle webhook (HMAC) | HMAC only |

### DEX/SWAP P2P Trading
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| POST | `/api/dex/wallets` | Create/link wallet | Authenticated |
| GET | `/api/dex/wallets` | List user wallets | Authenticated |
| GET | `/api/dex/wallets/<address>/balance` | Get wallet balance | Authenticated |
| POST | `/api/dex/orders` | Create buy/sell order | Authenticated |
| GET | `/api/dex/orders` | List orders (filterable) | Authenticated |
| GET | `/api/dex/orders/<uuid:id>` | Get order details | Authenticated |
| PATCH | `/api/dex/orders/<uuid:id>/cancel` | Cancel order | Authenticated |
| GET | `/api/dex/orderbook?isin=<ISIN>` | Get order book | Authenticated |
| POST | `/api/dex/swaps` | Create swap | Authenticated |
| GET | `/api/dex/swaps` | List swaps | Authenticated |
| GET | `/api/dex/swaps/<uuid:id>` | Get swap details | Authenticated |
| GET | `/api/dex/trades` | List executed trades | Authenticated |

### Blockchain Events
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| POST | `/api/issuance/events/ingest` | Ingest blockchain event | `ops`, `issuer` |

### Compliance (KYC/AML)
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| GET | `/api/compliance/profile` | Get investor profile | Authenticated |
| PATCH | `/api/compliance/profile` | Update investor profile | Authenticated |
| GET | `/api/compliance/documents` | List KYC documents | Authenticated |
| POST | `/api/compliance/documents` | Upload KYC document | Authenticated |
| GET | `/api/compliance/aml-checks` | Get AML check results | `ops`, `issuer` |
| GET | `/api/compliance/audit-logs` | Query audit logs | `ops` |

### Notifications
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| GET | `/api/notifications` | List user notifications | Authenticated |
| GET | `/api/notifications/preferences` | Get notification preferences | Authenticated |
| PATCH | `/api/notifications/preferences` | Update notification preferences | Authenticated |

### Reports & Analytics
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| GET | `/api/reports/trading` | Trading activity report | Authenticated |
| GET | `/api/reports/settlement` | Settlement activity report | `ops`, `issuer` |
| GET | `/api/reports/issuance` | Token issuance report | `ops`, `issuer` |
| GET | `/api/reports/reconciliation` | Blockchain reconciliation report | `ops` |

### System Health
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/health` | Basic health check | None |
| GET | `/api/ready` | Readiness check (database, cache) | None |
| GET | `/api/metrics` | System metrics | None |

### File Storage
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| POST | `/api/storage/upload` | Upload file (KYC documents, contracts) | Authenticated |
| GET | `/api/storage/files` | List stored files | Authenticated |
| GET | `/api/storage/files/<id>` | Download file | Authenticated |
| DELETE | `/api/storage/files/<id>/delete` | Delete file | Authenticated |

### Outbound Webhooks
| Method | Endpoint | Description | RBAC |
|--------|----------|-------------|------|
| GET | `/api/webhooks/outbound` | List webhook subscriptions | Authenticated |
| POST | `/api/webhooks/outbound` | Create webhook subscription | Authenticated |
| PATCH | `/api/webhooks/outbound/<id>` | Update webhook subscription | Authenticated |
| DELETE | `/api/webhooks/outbound/<id>` | Delete webhook subscription | Authenticated |
| GET | `/api/webhooks/outbound/<id>/deliveries` | List delivery history | Authenticated |
| POST | `/api/webhooks/outbound/deliveries/<id>/retry` | Retry failed delivery | Authenticated |

## Security & Access Control

### Authentication
- **JWT Bearer Tokens** - All endpoints (except webhooks) require JWT authentication
- **Token Refresh** - Long-lived sessions via refresh tokens
- **Webhook Authentication** - HMAC SHA256 signature verification (no JWT required)

### Role-Based Access Control (RBAC)

| Group | Permissions |
|-------|-------------|
| `issuer` | POST issuance, settlement, corporate actions |
| `reporter` | POST derivatives |
| `ops` | All Clearstream write operations |

**Bootstrap Groups:**
```cmd
python manage.py bootstrap_groups
```

**Assign User to Group:**
```cmd
python manage.py shell
```
```python
from django.contrib.auth.models import User, Group
user = User.objects.get(username='admin')
group = Group.objects.get(name='issuer')
group.user_set.add(user)
```

### Rate Limiting
- **Global Throttling**: 
  - Authenticated users: `100/min` (configurable via `RATE_LIMIT_USER`)
  - Anonymous users: `20/min` (configurable via `RATE_LIMIT_ANON`)
- **Per-Endpoint**: Critical POST endpoints limited to `60/min` per user

### Idempotency
- Use `Idempotency-Key` header on all POST requests
- Prevents duplicate operations
- Supported on: issuance, settlement, corporate actions, Clearstream writes
- Keys are cached for 24 hours

### Webhook Security
- **HMAC SHA256** signature verification
- **Timestamp validation** (±300 seconds)
- **Nonce replay protection** (unique nonces stored)
- **Required Headers**: 
  - `X-Signature: sha256=<hex>`
  - `X-Timestamp: <epoch or ISO8601>`
  - `X-Nonce: <unique-string>`

### Observability
- **Request Tracking**: All responses include `X-Request-ID` header
- **Session Activity**: Lightweight session tracking for authenticated requests

## Quick Start

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git (optional)

### Installation

#### 1. Clone and Setup Environment

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Configure Environment

```cmd
copy .env.example .env
```

Edit `.env` file with your configuration. See [Environment Setup Guide](docs/env-setup.md) for details.

#### 3. Setup PostgreSQL Database

**Install PostgreSQL:**
- Download from [PostgreSQL Official Website](https://www.postgresql.org/download/windows/)
- During installation, remember the password for the `postgres` user

**Create Database:**
```cmd
psql -U postgres
```
```sql
CREATE DATABASE dtcc_sto_db;
\q
```

**Configure Connection:**
Add to your `.env` file:
```bash
DATABASE_URL=postgres://postgres:your_password@localhost:5432/dtcc_sto_db
```

> 📖 **Detailed Setup**: See [PostgreSQL Setup Guide](docs/postgresql-setup.md) for comprehensive instructions

#### 4. Run Migrations

```cmd
cd backend
.venv\Scripts\activate
python manage.py migrate
python manage.py createsuperuser
python manage.py bootstrap_groups
```

#### 5. Start Development Server

```cmd
python manage.py runserver
```

**Access the API:**
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- API Schema: http://localhost:8000/api/schema/

> 📖 **Windows-Specific Help**: See [Windows Setup Guide](docs/windows-setup.md) for detailed Windows instructions

## Deployment

### Vercel Serverless Deployment

This project is optimized for Vercel serverless functions (no Docker required).

#### 1. Prerequisites
- Vercel account
- External PostgreSQL database (Neon, Supabase, or AWS RDS)
- External Redis instance (Upstash or AWS ElastiCache)

#### 2. Vercel Configuration Files
The following files are already configured:
- `api/index.py` - Django WSGI entry point for serverless function
- `backend/vercel.json` - Routes configuration
- `backend/requirements.txt` - Python dependencies

#### 3. Environment Variables
Configure in Vercel Project → Settings → Environment Variables:

**Required:**
   ```bash
DJANGO_SETTINGS_MODULE=config.settings
DEBUG=false
ALLOWED_HOSTS=.vercel.app,<your-domain>
DATABASE_URL=postgres://user:pass@host:5432/dbname
REDIS_URL=redis://host:port
DJANGO_SECRET_KEY=<strong-random-secret>
```

**Optional (as needed):**
   ```bash
EUROCLEAR_API_BASE=https://api.euroclear.com
EUROCLEAR_API_KEY=<your-key>
CLEARSTREAM_PMI_BASE=https://api.clearstream.com
CLEARSTREAM_PMI_KEY=<your-key>
WEBHOOK_SECRET=<hmac-secret>
SENDGRID_API_KEY=<your-sendgrid-api-key>
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=DTCC STO Backend
```

#### 4. Database Migrations
Run migrations against your production database:

```cmd
set DATABASE_URL=postgres://...
cd backend
python manage.py migrate
```

#### 5. Deploy
```cmd
   vercel
   vercel --prod
   ```

#### 6. Verify Deployment
- ✅ API Documentation: `https://<project>.vercel.app/api/docs/`
- ✅ ReDoc: `https://<project>.vercel.app/api/redoc/`
- ✅ Test JWT authentication flow
- ✅ Test protected endpoints

## API Usage Examples

### Authentication

**Obtain JWT Token:**
```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"youruser","password":"yourpass"}'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Use Token:**
```bash
curl -X GET http://localhost:8000/api/issuance/?isin=US0378331005 \
  -H 'Authorization: Bearer <access-token>'
```

### Quick Test Examples

> 📖 **Complete Testing Guide**: See [API Testing Guide](docs/api-testing-guide.md) for comprehensive examples

**1. Token Issuance (requires `issuer` group):**
```bash
curl -X POST http://localhost:8000/api/issuance/ \
  -H 'Authorization: Bearer <access>' \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-1' \
  -d '{
    "isin": "US0378331005",
    "investorAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "amount": "1000",
    "offeringType": "RegD"
  }'
```

**2. Derivative Reporting (requires `reporter` group):**
```bash
curl -X POST http://localhost:8000/api/derivatives/ \
  -H 'Authorization: Bearer <access>' \
  -H 'Content-Type: application/json' \
  -d '{
    "isin": "US0378331005",
    "upi": "UPI-TEST-001",
    "effectiveDate": "2025-01-01",
    "executionTimestamp": "2025-01-01T00:00:00Z",
    "notionalAmount": "1000000",
    "notionalCurrency": "USD",
    "productType": "SWAP",
    "underlyingAsset": "AAPL",
    "action": "NEW"
  }'
```

**3. Settlement Creation (requires `issuer` group):**
```bash
curl -X POST http://localhost:8000/api/settlement/ \
  -H 'Authorization: Bearer <access>' \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-2' \
  -d '{
    "isin": "US0378331005",
    "quantity": "10"
  }'
```

**4. Corporate Action (requires `issuer` group):**
```bash
curl -X POST http://localhost:8000/api/corporate-actions/ \
  -H 'Authorization: Bearer <access>' \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-3' \
  -d '{
    "isin": "US0378331005",
    "type": "DIVIDEND",
    "recordDate": "2025-12-31",
    "amountPerShare": "1.00",
    "currency": "USD"
  }'
```

**5. Clearstream Account (requires `ops` or `issuer` group):**
```bash
curl -X POST http://localhost:8000/api/clearstream/accounts \
  -H 'Authorization: Bearer <access>' \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: acct-1' \
  -d '{
    "csd_participant": "P1",
    "csd_account": "ACC-001"
  }'
```

## Configuration

### Environment Variables

> 📖 **Complete Guide**: See [Environment Setup Guide](../ENVIRONMENT_SETUP.md) or [ENV_SETUP.md](ENV_SETUP.md) for detailed configuration

**Quick Setup:**
1. Copy `.env.example` to `.env`
2. Fill in required variables (see `ENV_SETUP.md`)
3. Required: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`

#### Core Settings
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes |
| `DJANGO_SECRET_KEY` | Django secret key (strong random string) | ✅ Yes |
| `DEBUG` | Debug mode (true/false) | No |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | Yes (prod) |
| `REDIS_URL` | Redis connection for Celery | No |

#### Integration Settings
| Variable | Description | Required |
|----------|-------------|----------|
| `EUROCLEAR_API_BASE` | Euroclear API base URL | No |
| `EUROCLEAR_API_KEY` | Euroclear API key | No |
| `CLEARSTREAM_PMI_BASE` | Clearstream PMI API base URL | No |
| `CLEARSTREAM_PMI_KEY` | Clearstream PMI API key | No |
| `WEBHOOK_SECRET` | HMAC secret for webhook verification | No |
| `QUICKNODE_URL` | QuickNode RPC endpoint | No |
| `ISSUANCE_CONTRACT_ADDRESS` | Smart contract address | No |
| `ISSUANCE_CONTRACT_ABI` | Contract ABI (JSON string or file path) | No |
| `BLOCKCHAIN_NETWORK` | Network name (BSC, Ethereum, Polygon) | No |
| `START_BLOCK_NUMBER` | Block number to start listening from | No |
| `WALLET_PRIVATE_KEY` | Private key for blockchain transactions | No |

#### Optional Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_USER` | User rate limit | `100/min` |
| `RATE_LIMIT_ANON` | Anonymous rate limit | `20/min` |
| `CORS_ALLOWED_ORIGINS` | CORS allowed origins | - |

## Database Management

### Initial Setup
```cmd
python manage.py migrate
python manage.py createsuperuser
python manage.py bootstrap_groups
```

### Creating New Migrations
```cmd
python manage.py makemigrations
python manage.py migrate
```

### Models Included
- `Settlement` - Settlement records (Euroclear/Clearstream)
- `CorporateAction` - Corporate action records
- `ClearstreamAccount` - Clearstream CSD accounts
- `Position` - Clearstream position balances
- `IdempotencyKey` - Idempotency key cache
- `ApiSession` - Session activity tracking
- `WebhookReplay` - Webhook nonce tracking

## API Response Format

All API responses follow a consistent envelope format:

**Success Response:**
```json
{
  "success": true,
  "timestamp": "2025-01-15T10:30:00Z",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message or validation errors",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Documentation

### Available Guides
- 📖 [Windows Setup Guide](docs/windows-setup.md) - Complete Windows development setup
- 📖 [PostgreSQL Setup Guide](docs/postgresql-setup.md) - Database configuration
- 📖 [Environment Setup Guide](docs/env-setup.md) - Environment variables reference
- 📖 [API Testing Guide](docs/api-testing-guide.md) - Comprehensive API testing examples

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Development

### Testing (Roadmap)
- Unit tests with pytest + pytest-django
- Integration tests with mocked external APIs (respx)
- Coverage target: ≥80% for core components

### CI/CD
- GitHub Actions workflow (`.github/workflows/ci.yml`)
- Automated system checks
- Security audit with `pip-audit`

## Important Notes

- ⚠️ **Euroclear/Clearstream clients** are currently stubbed - replace with real HTTP implementations when credentials are available
- ✅ **PostgreSQL required** - SQLite is not supported
- ✅ **All responses** use the standard envelope format: `{ success, data?, error?, timestamp }`
- ✅ **Idempotency** is supported on all POST endpoints via `Idempotency-Key` header
- ✅ **Windows development** is fully supported with comprehensive documentation

## Support

For issues, questions, or contributions, please refer to the project documentation or contact the development team.

---

**Built with** Django 5.2 • DRF 3.16 • PostgreSQL • Redis • Celery
