# 📚 Bill Bitts / NEO Bank Payment Integration MVP - Complete Explainer

## 🎯 **What We Built**

This integration connects your Django backend to the Bill Bitts/NEO Bank payment processing system, enabling real-time cryptocurrency and fiat payments for DPO ERC-1400 Security Token purchases.

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DPO CONTENT CREATOR NOTEBOOK                     │
│  (Frontend Logic - Marketplace Control Panel)                       │
│  • Lists security tokens                                             │
│  • Creates orders                                                    │
│  • Tracks settlements                                                │
└────────────────┬────────────────────────────────────────────────────┘
                 │ HTTP API Calls (localhost:8000)
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DJANGO BACKEND (New!)                          │
│  apps/payments/ - Bill Bitts Integration                            │
│  ├─ models.py → PaymentProfile, Transaction (Database)              │
│  ├─ services.py → BillBittsClient (RSA-2048 Signing)                │
│  ├─ views.py → Webhook Listener + Trade Execution API               │
│  └─ omnisend_service.py → Marketing Automation                      │
└────────────────┬────────────────────────────────────────────────────┘
                 │
      ┌──────────┴────────────┐
      │                       │
      ▼                       ▼
┌──────────────────┐  ┌──────────────────────┐
│  BILL BITTS API  │  │  OMNISEND MARKETING  │
│  (Crypto/Fiat)   │  │  (Email Automation)  │
│                  │  │                      │
│  • CPRN Registration │  • Trade Confirmations│
│  • Payment Processing│  │  • Welcome Emails     │
│  • Settlement (T+2)  │  │  • Payment Receipts   │
└──────────────────┘  └──────────────────────┘
```

---

## 📁 **File-by-File Breakdown**

### 1. **models.py** - Data Layer
**Purpose:** Defines how payment data is stored in the database

```python
# Two main models:

class PaymentProfile(models.Model):
    """Links Django users to Bill Bitts banking"""
    - cprn_number: Unique ID from Bill Bitts (like a bank account number)
    - web3_wallet_address: User's Ethereum wallet (for ERC-1400 token delivery)
    - neo_balance: Current fiat balance from NEO Bank
    - is_verified: Security flag

class Transaction(models.Model):
    """Tracks individual payments"""
    - transaction_id: Unique ID from NEO Bank
    - amount, currency: Payment details
    - status: PENDING → SUCCESS → SETTLED
    - token_contract_address, token_symbol: ERC-1400 Security Token purchased
    - webhook_payload: Raw data from bank (for auditing)
```

**Why it matters:** Every payment is recorded permanently. If something goes wrong, you have a complete audit trail.

---

### 2. **services.py** - Bill Bitts API Client
**Purpose:** Securely communicates with Bill Bitts using RSA digital signatures

```python
class BillBittsClient:
    def sign_payload(self, data):
        """Signs requests with RSA-2048 private key"""
        # This proves the request came from YOU
        # Bill Bitts verifies the signature before processing
    
    def create_registration(self, user_data):
        """Creates CPRN for a new user"""
        # Returns: {'cprn': 'CPRN-ABC123', 'status': 'success'}
    
    def initiate_payment(self, payment_data):
        """Starts a payment transaction"""
        # Returns: {'tx_id': 'TXN-XYZ789', 'status': 'pending'}
```

**Security Analogy:** 
- Your **private key** = Your signature on a check
- Bill Bitts **public key** = Verifies it's really you
- If someone steals your API request, they can't forge your signature

---

### 3. **views.py** - Real-Time Event Handlers
**Purpose:** Receives notifications from NEO Bank when payments settle

#### 3a. **`neo_bank_webhook`** - The Listener
```python
@csrf_exempt  # External service can't send CSRF token
def neo_bank_webhook(request):
    """
    NEO Bank calls THIS when:
    - Payment clears (SUCCESS)
    - Funds settle in account (SETTLED)
    - Payment fails (FAILED)
    """
    # 1. Parse the incoming notification
    data = json.loads(request.body)
    
    # 2. Find the user by their CPRN
    profile = PaymentProfile.objects.get(cprn_number=data['cprn'])
    
    # 3. Update their balance
    profile.neo_balance += float(data['amount'])
    profile.save()
    
    # 4. Trigger marketing email
    omni = OmnisendClient()
    omni.trigger_trade_confirmation(user.email, amount, token_symbol)
```

**Real-World Flow:**
1. User clicks "Buy Security Token" for $500
2. Your frontend calls `/api/execute-trade/`
3. Bill Bitts processes the payment (takes 2-30 seconds)
4. NEO Bank calls `/webhooks/neo-payment/` → "Payment SUCCESS"
5. Your Django updates balance, sends confirmation email
6. ERC-1400 Security Token is transferred to user's wallet

#### 3b. **`execute_trade`** - The Initiator
```python
def execute_trade(request):
    """
    Frontend calls THIS to start a payment
    """
    # 1. Get user's CPRN
    profile = PaymentProfile.objects.get(user=request.user)
    
    # 2. Call Bill Bitts API
    client = BillBittsClient()
    result = client.initiate_payment({
        'cprn': profile.cprn_number,
        'amount': '500.00',
        'description': 'ERC-1400 Security Token Purchase: DPO-STO-001'
    })
    
    # 3. Return transaction ID to frontend
    return JsonResponse({'tx_id': result['tx_id']})
```

---

### 4. **omnisend_service.py** - Marketing Automation
**Purpose:** Sends branded emails automatically when events happen

```python
class OmnisendClient:
    def trigger_trade_confirmation(self, email, amount, token_symbol):
        """
        Sends 'Security Token Trade Success' event to Omnisend
        
        Omnisend then:
        1. Looks for an Automation Workflow named "Security Token Trade Success"
        2. Sends the pre-designed email template
        3. Includes dynamic data: {amount}, {token_symbol}
        """
        payload = {
            "eventName": "Security Token Trade Success",
            "email": email,
            "properties": {
                "trade_amount": amount,
                "token_symbol": token_symbol
            }
        }
        # POST to Omnisend API
```

**Setup in Omnisend Dashboard:**
1. Create Automation Workflow
2. Trigger = "Security Token Trade Success" (custom event)
3. Design email with placeholders: `{{trade_amount}}`, `{{token_symbol}}`
4. When webhook calls `trigger_trade_confirmation()`, email sends automatically

---

## 🔧 **The Setup Script (SETUP_PAYMENTS_MVP.ps1)**

### **What It Does (Step-by-Step):**

#### **STEP 1: Install Dependencies**
```powershell
pip install -q -r requirements.txt
pip install -q pycryptodome  # For RSA signing
```
**Installs:**
- Django framework
- `pycryptodome` - Encryption library for RSA signatures
- `requests` - For API calls
- Database drivers (PostgreSQL support)

#### **STEP 2: Check Database Configuration**
```powershell
# Looks for DATABASE_URL environment variable
# If not found, creates .env file with SQLite fallback
```
**Creates `.env` file with:**
```ini
DATABASE_URL=sqlite:///./db.sqlite3
BILLBITTS_API_URL=https://api.billbitcoins.com
BILLBITTS_API_KEY=your-api-key-here
OMNISEND_API_KEY=your-omnisend-api-key-here
```

#### **STEP 3: Database Migrations**
```powershell
python manage.py makemigrations payments
python manage.py migrate
```
**Creates database tables:**
- `payment_profiles` - Stores CPRN, wallet addresses, balances
- `payment_transactions` - Logs every payment with timestamps

**Migration = Blueprint for Database**
- `makemigrations` → Creates the blueprint
- `migrate` → Executes the blueprint (creates actual tables)

#### **STEP 4: Collect Static Files**
```powershell
python manage.py collectstatic --noinput
```
**Gathers:** CSS, JavaScript, images for Django admin panel

---

## 🚀 **How to Use the Setup Script**

### **Basic Usage:**
```powershell
cd C:\...\DPO_AI_CRM_LEAD_MGMT\external\dtcc-django
.\SETUP_PAYMENTS_MVP.ps1
```

### **Advanced Options:**
```powershell
# Skip installation (if packages already installed)
.\SETUP_PAYMENTS_MVP.ps1 -SkipInstall

# Skip migrations (if database already configured)
.\SETUP_PAYMENTS_MVP.ps1 -SkipMigrations

# Auto-start Django server after setup
.\SETUP_PAYMENTS_MVP.ps1 -StartServer
```

---

## 📡 **API Endpoints Created**

### 1. **Webhook Listener** (for NEO Bank)
```
POST /webhooks/neo-payment/
```
**Purpose:** NEO Bank calls this when payments settle  
**Authentication:** None (webhook signature verification recommended)  
**Payload:**
```json
{
  "cprn": "CPRN-ABC12345",
  "status": "SUCCESS",
  "amount": "250.00",
  "tx_id": "TXN-XYZ789",
  "currency": "USD"
}
```

### 2. **Trade Execution** (for Frontend)
```
POST /api/execute-trade/
```
**Purpose:** Notebook/frontend calls this to start a payment  
**Authentication:** Django session/JWT required  
**Payload:**
```json
{
  "token_contract_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "token_symbol": "DPO-STO",
  "amount": "500.00",
  "currency": "USD"
}
```
**Response:**
```json
{
  "status": "success",
  "transaction_id": "TXN-ABC123"
}
```

---

## 🔐 **Security Features**

### 1. **RSA-2048 Digital Signatures**
```python
# Your private key signs the request
signature = sign_payload(data)

# Bill Bitts verifies with your public key
# If tampered, signature won't match → rejected
```

### 2. **CPRN (Customer Presentment Registration Number)**
- Unique ID per user (like a bank account number)
- Prevents accidental cross-user payments
- Required for all Bill Bitts API calls

### 3. **Webhook Payload Logging**
```python
# Every webhook is stored in Transaction.webhook_payload
# If dispute arises, you have complete audit trail
```

---

## 🧪 **Testing the Integration**

### **Test Flow (After Setup):**

1. **Start Django Server:**
   ```powershell
   python manage.py runserver
   ```

2. **Run Notebook Cell 57** (Quick-Start Automated Test)
   - Initializes all components
   - Tests Django API connection
   - Shows: `✅ Django API OK! (http://localhost:8000/api)`

3. **Run Cell 55** (Launch Interactive Menu)
   ```python
   show_marketplace_menu()
   ```
   - Click "🧪 Run Tests" → Validates backend connection
   - Click "🛒 Create Order" → Test payment flow
   - Click "🏦 Settlements" → View transaction history

### **Manual API Test (using PowerShell):**
```powershell
# Test webhook endpoint
$body = @{
    cprn = "CPRN-TEST123"
    status = "SUCCESS"
    amount = "100.00"
    tx_id = "TXN-TEST001"
    currency = "USD"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/webhooks/neo-payment/" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

---

## ⚙️ **Environment Variables (.env file)**

```ini
# Django Core
DEBUG=true
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///./db.sqlite3
# Production: postgres://user:password@localhost:5432/dbname

# Bill Bitts Payment Gateway
BILLBITTS_API_URL=https://api.billbitcoins.com
BILLBITTS_API_KEY=pk_live_XXXXXXXX
BILLBITTS_PRIVATE_KEY_PATH=./keys/billbitts_private.pem

# Omnisend Marketing
OMNISEND_API_KEY=6abc123def456-XXXXXXXX

# Redis (Optional - for production caching)
REDIS_URL=redis://localhost:6379/0
```

---

## 🐛 **Common Issues & Solutions**

### **Issue 1: "ModuleNotFoundError: No module named 'dj_database_url'"**
**Solution:**
```powershell
pip install dj-database-url django
```

### **Issue 2: "DATABASE_URL environment variable is required"**
**Solution:** Create `.env` file or run setup script (it auto-creates one)

### **Issue 3: "django.core.exceptions.ImproperlyConfigured"**
**Solution:** 
```powershell
# Ensure you're in the Django project directory
cd C:\...\DPO_AI_CRM_LEAD_MGMT\external\dtcc-django
python manage.py migrate
```

### **Issue 4: "Port 8000 already in use"**
**Solution:**
```powershell
# Run on different port
python manage.py runserver 8001
# Update notebook config.django_api_url = "http://localhost:8001/api"
```

---

## 📈 **Next Steps After Setup**

1. **Create Django Superuser:**
   ```powershell
   python manage.py createsuperuser
   # Enter: username, email, password
   ```

2. **Access Django Admin:**
   ```
   http://localhost:8000/admin/
   ```
   - View all payment profiles
   - Monitor transactions in real-time
   - Manually adjust balances if needed

3. **Configure Bill Bitts API:**
   - Get API keys from Bill Bitts dashboard
   - Generate RSA key pair: `ssh-keygen -t rsa -b 2048`
   - Upload public key to Bill Bitts portal
   - Add private key path to `.env`

4. **Set Up Omnisend Automation:**
   - Create "NFT Trade Success" workflow
   - Design branded email template
   - Add API key to `.env`

5. **Test Full Flow:**
   - Run notebook Cell 57
   - Create test payment via Cell 55
   - Check email inbox for Omnisend confirmation
   - Verify transaction in Django admin

---

## 🎓 **Learning Points**

### **What You've Learned:**

1. **Webhook Architecture**
   - External services (NEO Bank) notify YOUR server
   - No polling needed - real-time updates
   - Like doorbell vs. checking door constantly

2. **Digital Signatures (RSA-2048)**
   - Private key = Your pen (keep secret!)
   - Public key = Signature verifier (share freely)
   - Tamper-proof: Change 1 byte → signature invalid

3. **Django Apps**
   - Modular structure: `apps/payments/` is self-contained
   - Each app has: models, views, URLs, admin
   - Reusable: Can copy to other Django projects

4. **Event-Driven Marketing**
   - Code event: `payment successful`
   - Omnisend automation: Triggered automatically
   - No manual email sending needed

5. **Database Migrations**
   - Version control for database schema
   - Can roll back if needed
   - Team members stay in sync

---

## 📝 **Quick Reference Commands**

```powershell
# Setup
cd external/dtcc-django
.\SETUP_PAYMENTS_MVP.ps1 -StartServer

# Development
python manage.py runserver              # Start server
python manage.py shell                  # Interactive Python shell
python manage.py createsuperuser        # Create admin account

# Database
python manage.py makemigrations         # Create migration files
python manage.py migrate                # Apply migrations
python manage.py showmigrations         # List all migrations

# Debugging
python manage.py check                  # Check for errors
python manage.py test                   # Run automated tests
python manage.py dbshell                # Direct database access
```

---

## 🎉 **Success Criteria**

You'll know it's working when:

✅ Django server starts without errors  
✅ Notebook Cell 57 shows: "✅ Django API OK!"  
✅ Admin panel loads at `http://localhost:8000/admin/`  
✅ Can create PaymentProfile in Django admin  
✅ Webhook test returns `200 OK`  
✅ Transaction appears in database after webhook call  

---

**Happy Building! 🚀**  
*For questions, check Django logs or webhook payload data in Transaction records.*
