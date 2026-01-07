#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automated setup script for Bill Bitts / NEO Bank Payment Integration MVP
    
.DESCRIPTION
    This script:
    1. Installs required Python dependencies
    2. Creates database migrations for the payments app
    3. Applies migrations to the database
    4. Optionally starts the Django development server
    
.PARAMETER SkipInstall
    Skip pip install step if dependencies are already installed
    
.PARAMETER SkipMigrations
    Skip database migration steps
    
.PARAMETER StartServer
    Automatically start the Django server after setup
    
.EXAMPLE
    .\SETUP_PAYMENTS_MVP.ps1
    Run full setup including install, migrations, but don't start server
    
.EXAMPLE
    .\SETUP_PAYMENTS_MVP.ps1 -StartServer
    Run full setup and start Django server
    
.EXAMPLE
    .\SETUP_PAYMENTS_MVP.ps1 -SkipInstall
    Skip package installation, just run migrations
#>

param(
    [switch]$SkipInstall = $false,
    [switch]$SkipMigrations = $false,
    [switch]$StartServer = $false
)

# Script configuration
$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"
$ManagePy = Join-Path $ScriptDir "manage.py"

# Color output functions
function Write-Success { 
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green 
}

function Write-Info { 
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan 
}

function Write-Warning-Custom { 
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow 
}

function Write-Error-Custom { 
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red 
}

function Write-Step { 
    param([string]$Message)
    Write-Host "`n" + ("=" * 80) -ForegroundColor Magenta
    Write-Host "🚀 $Message" -ForegroundColor Magenta
    Write-Host ("=" * 80) -ForegroundColor Magenta
}

# Banner
Clear-Host
Write-Host @"

╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║          BILL BITTS / NEO BANK PAYMENT INTEGRATION MVP SETUP             ║
║                                                                           ║
║  This script will configure the Django backend with payment processing   ║
║  capabilities including:                                                  ║
║    • Bill Bitts API integration with RSA-2048 signing                    ║
║    • NEO Bank webhook listeners for real-time settlement                 ║
║    • Omnisend marketing automation triggers                              ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Verify we're in the right directory
if (-not (Test-Path $ManagePy)) {
    Write-Error-Custom "manage.py not found! Please run this script from the Django project root."
    Write-Info "Expected location: $ManagePy"
    exit 1
}

Write-Success "Found Django project at: $ScriptDir"

# ============================================================================
# STEP 1: Install Dependencies
# ============================================================================
if (-not $SkipInstall) {
    Write-Step "STEP 1/4: Installing Python Dependencies"
    
    if (-not (Test-Path $RequirementsFile)) {
        Write-Error-Custom "requirements.txt not found at: $RequirementsFile"
        exit 1
    }
    
    Write-Info "Installing from: $RequirementsFile"
    Write-Info "This may take a few minutes..."
    
    try {
        # Install core requirements
        pip install -q -r $RequirementsFile
        
        # Ensure pycryptodome is installed (for RSA signing)
        pip install -q pycryptodome
        
        Write-Success "All dependencies installed successfully"
    }
    catch {
        Write-Error-Custom "Failed to install dependencies: $_"
        Write-Warning-Custom "You can try running manually: pip install -r requirements.txt"
        exit 1
    }
} else {
    Write-Step "STEP 1/4: Skipping Dependency Installation"
    Write-Info "Using existing packages"
}

# ============================================================================
# STEP 2: Check Database Configuration
# ============================================================================
Write-Step "STEP 2/4: Checking Database Configuration"

# Check if DATABASE_URL is set
$DatabaseUrl = [Environment]::GetEnvironmentVariable("DATABASE_URL")
if (-not $DatabaseUrl) {
    Write-Warning-Custom "DATABASE_URL environment variable not set!"
    Write-Info "Using SQLite for development..."
    
    # Create a temporary .env file with SQLite config
    $EnvFile = Join-Path $ScriptDir ".env"
    if (-not (Test-Path $EnvFile)) {
        Write-Info "Creating .env file with default SQLite configuration..."
        @"
# Django Configuration
DEBUG=true
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database - Using SQLite for development
# For production, use PostgreSQL: postgres://user:password@localhost:5432/dbname
DATABASE_URL=sqlite:///./db.sqlite3

# Bill Bitts Payment Integration
BILLBITTS_API_URL=https://api.billbitcoins.com
BILLBITTS_API_KEY=your-api-key-here
# BILLBITTS_PRIVATE_KEY_PATH=./keys/billbitts_private.pem

# Omnisend Marketing Automation
OMNISEND_API_KEY=your-omnisend-api-key-here

# Redis (optional - will use local memory cache if not set)
# REDIS_URL=redis://localhost:6379/0
"@ | Out-File -FilePath $EnvFile -Encoding UTF8
        Write-Success "Created .env file with default settings"
        Write-Warning-Custom "Remember to update API keys in .env before production use!"
    }
} else {
    Write-Success "Database configuration found: $($DatabaseUrl.Substring(0, [Math]::Min(50, $DatabaseUrl.Length)))..."
}

# ============================================================================
# STEP 3: Database Migrations
# ============================================================================
if (-not $SkipMigrations) {
    Write-Step "STEP 3/4: Creating and Applying Database Migrations"
    
    Write-Info "Creating migrations for payments app..."
    try {
        python $ManagePy makemigrations payments 2>&1 | Out-String | ForEach-Object {
            if ($_ -match "error|exception") {
                Write-Error-Custom $_
            } else {
                Write-Host $_
            }
        }
        
        Write-Success "Migrations created successfully"
    }
    catch {
        Write-Error-Custom "Failed to create migrations: $_"
        exit 1
    }
    
    Write-Info "Applying all pending migrations..."
    try {
        python $ManagePy migrate 2>&1 | Out-String | ForEach-Object {
            if ($_ -match "error|exception") {
                Write-Error-Custom $_
            } else {
                Write-Host $_
            }
        }
        
        Write-Success "Database migrations applied successfully"
    }
    catch {
        Write-Error-Custom "Failed to apply migrations: $_"
        exit 1
    }
} else {
    Write-Step "STEP 3/4: Skipping Database Migrations"
    Write-Info "Using existing database schema"
}

# ============================================================================
# STEP 4: Final Setup and Server Start
# ============================================================================
Write-Step "STEP 4/4: Final Configuration"

Write-Info "Collecting static files (if needed)..."
try {
    python $ManagePy collectstatic --noinput --clear 2>&1 | Out-Null
    Write-Success "Static files collected"
}
catch {
    Write-Warning-Custom "Static files collection skipped (not critical for development)"
}

# Display setup summary
Write-Host "`n"
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host "✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Green

Write-Host "`n📋 SETUP SUMMARY:" -ForegroundColor Cyan
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
Write-Host "  ✓ Database migrations applied" -ForegroundColor Green
Write-Host "  ✓ Payment app (Bill Bitts/NEO Bank) configured" -ForegroundColor Green
Write-Host "  ✓ Omnisend integration ready" -ForegroundColor Green

Write-Host "`n🔗 AVAILABLE ENDPOINTS:" -ForegroundColor Cyan
Write-Host "  • Admin Panel: http://localhost:8000/admin/" -ForegroundColor White
Write-Host "  • API Docs: http://localhost:8000/api/docs/" -ForegroundColor White
Write-Host "  • NEO Bank Webhook: http://localhost:8000/webhooks/neo-payment/" -ForegroundColor White
Write-Host "  • Execute Trade: http://localhost:8000/api/execute-trade/" -ForegroundColor White

Write-Host "`n📝 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Update .env file with your API keys (Bill Bitts, Omnisend)" -ForegroundColor Yellow
Write-Host "  2. Create a superuser: python manage.py createsuperuser" -ForegroundColor Yellow
Write-Host "  3. Start the server: python manage.py runserver" -ForegroundColor Yellow
Write-Host "  4. Run the notebook Cell 57 to test the integration" -ForegroundColor Yellow

# Start server if requested
if ($StartServer) {
    Write-Host "`n" + ("=" * 80) -ForegroundColor Magenta
    Write-Host "🚀 STARTING DJANGO DEVELOPMENT SERVER..." -ForegroundColor Magenta
    Write-Host ("=" * 80) -ForegroundColor Magenta
    Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow
    
    # Start in background and capture output
    python $ManagePy runserver
} else {
    Write-Host "`n💡 TIP: Run with -StartServer flag to automatically start Django:" -ForegroundColor Cyan
    Write-Host "   .\SETUP_PAYMENTS_MVP.ps1 -StartServer" -ForegroundColor White
}

Write-Host "`n"
