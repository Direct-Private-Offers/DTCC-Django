# Railway Production Environment Variables

## Complete Production Configuration

This guide lists **ALL** environment variables needed for a full production deployment.

---

## 🚀 Quick Deploy Script

Save this as `railway-setup.sh` and run it:

```bash
#!/bin/bash

# Core Required Variables
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
railway variables set ENVIRONMENT=production

# Security Settings
railway variables set SECURE_SSL_REDIRECT=True
railway variables set SECURE_HSTS_SECONDS=31536000

# Blockchain Configuration
railway variables set QUICKNODE_URL=YOUR_QUICKNODE_URL_HERE
railway variables set BLOCKCHAIN_RPC_URL=YOUR_QUICKNODE_URL_HERE
railway variables set BLOCKCHAIN_NETWORK=arbitrum-nova
railway variables set START_BLOCK_NUMBER=YOUR_START_BLOCK_HERE

# Smart Contract Addresses
railway variables set ISSUANCE_CONTRACT_ADDRESS=YOUR_CONTRACT_ADDRESS
railway variables set STO_CONTRACT_ADDRESS=YOUR_CONTRACT_ADDRESS
railway variables set DERIVATIVES_REPORTER_CONTRACT_ADDRESS=YOUR_CONTRACT_ADDRESS
railway variables set EUROCLEAR_BRIDGE_CONTRACT_ADDRESS=YOUR_CONTRACT_ADDRESS
railway variables set WALLET_PRIVATE_KEY=YOUR_WALLET_PRIVATE_KEY

# API Integrations
railway variables set EUROCLEAR_API_BASE=https://api.euroclear.com
railway variables set EUROCLEAR_API_KEY=YOUR_EUROCLEAR_KEY
railway variables set CLEARSTREAM_PMI_BASE=https://api.clearstream.com
railway variables set CLEARSTREAM_PMI_KEY=YOUR_CLEARSTREAM_KEY
railway variables set XETRA_API_BASE=https://api.xetra.com
railway variables set XETRA_API_KEY=YOUR_XETRA_KEY

# Payment Integration
railway variables set BILLBITTS_API_KEY=YOUR_BILLBITTS_KEY
railway variables set BILLBITTS_PRIVATE_KEY_PATH=/app/keys/billbitts.pem

# Email Service (choose one)
railway variables set OMNISEND_API_KEY=YOUR_OMNISEND_KEY
# OR
# railway variables set SENDGRID_API_KEY=YOUR_SENDGRID_KEY

# CORS (Frontend)
railway variables set CORS_ALLOWED_ORIGINS=https://www.directprivateoffers.net,https://directprivateoffers.net

echo "All variables set! Run: railway up --service web"
```

---

## 📋 Variable Categories

### 1. Core Required (Must Have)

```bash
DJANGO_SETTINGS_MODULE=config.settings
DJANGO_SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
ALLOWED_HOSTS=.railway.app
ENVIRONMENT=production
```

### 2. Database (Auto-Provided by Railway)

```bash
DATABASE_URL=<auto-injected-by-railway>
```

### 3. Security Settings

```bash
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
CORS_ALLOWED_ORIGINS=https://www.directprivateoffers.net,https://directprivateoffers.net
```

### 4. Blockchain & Smart Contracts

```bash
QUICKNODE_URL=https://your-endpoint.arbitrum-nova.quiknode.pro/xxxxx/
BLOCKCHAIN_RPC_URL=https://your-endpoint.arbitrum-nova.quiknode.pro/xxxxx/
BLOCKCHAIN_NETWORK=arbitrum-nova
START_BLOCK_NUMBER=12345678

# Contract Addresses
ISSUANCE_CONTRACT_ADDRESS=0x...
STO_CONTRACT_ADDRESS=0x...
DERIVATIVES_REPORTER_CONTRACT_ADDRESS=0x...
EUROCLEAR_BRIDGE_CONTRACT_ADDRESS=0x...

# Wallet
WALLET_PRIVATE_KEY=0x...
```

### 5. Financial Market APIs

**Euroclear**
```bash
EUROCLEAR_API_BASE=https://api.euroclear.com
EUROCLEAR_API_KEY=your-api-key
EUROCLEAR_TIMEOUT=30
```

**Clearstream**
```bash
CLEARSTREAM_PMI_BASE=https://api.clearstream.com
CLEARSTREAM_PMI_KEY=your-api-key
CLEARSTREAM_PARTICIPANT_ID=your-participant-id
CLEARSTREAM_TIMEOUT=30
```

**XETRA (Deutsche Börse)**
```bash
XETRA_API_BASE=https://api.xetra.com
XETRA_API_KEY=your-api-key
XETRA_PARTICIPANT_ID=your-participant-id
XETRA_TIMEOUT=30
```

### 6. Payment Integration

```bash
BILLBITTS_API_KEY=your-billbitts-api-key
BILLBITTS_API_URL=https://api.billbitcoins.com
BILLBITTS_PRIVATE_KEY_PATH=/app/keys/billbitts.pem
```

**Note:** For the private key file, you'll need to upload it to Railway or use secrets management.

### 7. Email Service (Choose One)

**Option A: Omnisend (Recommended)**
```bash
OMNISEND_API_KEY=your-omnisend-key
```

**Option B: SendGrid**
```bash
SENDGRID_API_KEY=SG.your-sendgrid-key
SENDGRID_FROM_EMAIL=noreply@your-domain.com
SENDGRID_FROM_NAME=DTCC STO Platform
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

### 8. Optional: Additional Integrations

**Neo Bank**
```bash
NEO_BANK_API_BASE=https://api.neobank.com/v1
NEO_BANK_API_KEY=your-neo-bank-key
NEO_BANK_MERCHANT_ID=your-merchant-id
NEO_BANK_TIMEOUT=30
```

**FX Market**
```bash
FX_MARKET_API_BASE=https://api.fxmarket.com/v1
FX_MARKET_API_KEY=your-fx-market-key
FX_MARKET_TIMEOUT=30
```

**IPFS (Document Storage)**
```bash
IPFS_ENABLED=false
IPFS_GATEWAY_URL=https://ipfs.io/ipfs/
IPFS_API_URL=http://localhost:5001
```

### 9. Rate Limiting

```bash
RATE_LIMIT_USER=100/min
RATE_LIMIT_ANON=20/min
```

---

## 🔐 Handling Private Keys

For `BILLBITTS_PRIVATE_KEY_PATH=/app/keys/billbitts.pem`:

### Option 1: Railway Volume (Recommended)

```bash
# Create a volume in Railway dashboard
# Upload your key file to the volume
# Set the path to match the volume mount point
railway variables set BILLBITTS_PRIVATE_KEY_PATH=/app/keys/billbitts.pem
```

### Option 2: Environment Variable (Less Secure)

```bash
# Store the key content directly in an environment variable
railway variables set BILLBITTS_PRIVATE_KEY="$(cat billbitts.pem)"
```

Then update your code to read from the variable instead of file.

### Option 3: Railway Secrets

Use Railway's secrets management for sensitive files.

---

## 📝 Set Variables Step-by-Step

### Step 1: Core Setup (Required)

```bash
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set DJANGO_SECRET_KEY=$(openssl rand -hex 32)
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=.railway.app
railway variables set ENVIRONMENT=production
```

### Step 2: Security (Recommended)

```bash
railway variables set SECURE_SSL_REDIRECT=True
railway variables set SECURE_HSTS_SECONDS=31536000
railway variables set CORS_ALLOWED_ORIGINS=https://your-frontend.com
```

### Step 3: Blockchain (If Using Smart Contracts)

```bash
railway variables set QUICKNODE_URL=your-quicknode-url
railway variables set BLOCKCHAIN_RPC_URL=your-quicknode-url
railway variables set BLOCKCHAIN_NETWORK=arbitrum-nova
railway variables set START_BLOCK_NUMBER=12345678
railway variables set ISSUANCE_CONTRACT_ADDRESS=0x...
railway variables set STO_CONTRACT_ADDRESS=0x...
railway variables set DERIVATIVES_REPORTER_CONTRACT_ADDRESS=0x...
railway variables set EUROCLEAR_BRIDGE_CONTRACT_ADDRESS=0x...
railway variables set WALLET_PRIVATE_KEY=0x...
```

### Step 4: Financial APIs (If Integrated)

```bash
railway variables set EUROCLEAR_API_BASE=https://api.euroclear.com
railway variables set EUROCLEAR_API_KEY=your-key
railway variables set CLEARSTREAM_PMI_BASE=https://api.clearstream.com
railway variables set CLEARSTREAM_PMI_KEY=your-key
railway variables set XETRA_API_BASE=https://api.xetra.com
railway variables set XETRA_API_KEY=your-key
```

### Step 5: Payment & Email

```bash
railway variables set BILLBITTS_API_KEY=your-key
railway variables set BILLBITTS_PRIVATE_KEY_PATH=/app/keys/billbitts.pem
railway variables set OMNISEND_API_KEY=your-key
```

### Step 6: Deploy!

```bash
railway up --service web
```

---

## ✅ Verify Configuration

```bash
# Check all variables are set
railway variables

# Should show all your configured variables
# DATABASE_URL should appear (auto-injected)
```

---

## 🔍 Troubleshooting

### Missing Variables Error?

Check the logs:
```bash
railway logs
```

Look for errors like:
- "DJANGO_SECRET_KEY environment variable must be set"
- "Missing required configuration"

### View Current Variables

```bash
railway variables
```

### Update a Variable

```bash
railway variables set VARIABLE_NAME=new-value
railway restart
```

### Remove a Variable

```bash
railway variables delete VARIABLE_NAME
```

---

## 📚 Related Documentation

- **Core Setup:** `RAILWAY-CORE-SETUP.md`
- **Quick Start:** `RAILWAY-QUICK-START.md`
- **Full Deployment:** `DEPLOYMENT.md`
- **Environment Template:** `.env.example`
- **Cleanup:** `CLEANUP-CHECKLIST.md`

---

**Last Updated:** 2026-01-30  
**Status:** Production-ready configuration guide
