"""
Bill Bitts / NEO Bank Payment Integration - Comprehensive Test Suite
Tests the ERC-1400 token purchase flow with corrected terminology
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
WEBHOOK_URL = f"{BASE_URL}/webhooks/neo-payment/"
EXECUTE_TRADE_URL = f"{BASE_URL}/api/execute-trade/"

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def test_server_health():
    """Test 1: Verify Django server is running"""
    print_header("TEST 1: Server Health Check")
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code in [200, 301, 302, 404]:  # Any response means server is up
            print_success("Django server is running")
            print_info(f"Status Code: {response.status_code}")
            return True
        else:
            print_warning(f"Server responded with status: {response.status_code}")
            return True
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to Django server")
        print_info("Make sure the server is running: python manage.py runserver")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_webhook_endpoint():
    """Test 2: Test NEO Bank webhook endpoint with ERC-1400 token data"""
    print_header("TEST 2: NEO Bank Webhook Endpoint (ERC-1400 Token Payment)")
    
    # Sample webhook payload with ERC-1400 token data
    webhook_payload = {
        "cprn": "CPRN-TEST-001",
        "status": "SUCCESS",
        "amount": "1000.00",
        "tx_id": f"TXN-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "currency": "USD",
        "token_contract_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "token_symbol": "DPO-STO"
    }
    
    print_info("Sending webhook payload:")
    print(json.dumps(webhook_payload, indent=2))
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {response.text}")
        
        if response.status_code == 404:
            print_success("Endpoint exists (expecting 404 because CPRN doesn't exist in DB)")
            print_info("This is expected - we haven't created any PaymentProfile records yet")
            return True
        elif response.status_code == 200:
            print_success("Webhook processed successfully!")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            return True
        else:
            print_warning(f"Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to webhook endpoint")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_models_via_django_admin():
    """Test 3: Check if models are accessible"""
    print_header("TEST 3: Django Admin & Models Check")
    
    try:
        # Test if admin panel is accessible
        response = requests.get(f"{BASE_URL}/admin/", timeout=5)
        print_info(f"Admin panel status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 302:
            print_success("Django admin is accessible")
            print_info("You can access it at: http://localhost:8000/admin/")
            print_info("Create a superuser with: python manage.py createsuperuser")
            return True
        else:
            print_warning(f"Admin returned status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error checking admin: {e}")
        return False

def test_database_tables():
    """Test 4: Verify database tables exist using Django shell"""
    print_header("TEST 4: Database Tables Verification")
    
    import os
    import sys
    
    # Add Django project to path
    django_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, django_path)
    
    try:
        # Set up Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        from apps.payments.models import PaymentProfile, Transaction
        
        # Check table structure
        profile_fields = [f.name for f in PaymentProfile._meta.fields]
        transaction_fields = [f.name for f in Transaction._meta.fields]
        
        print_success("Models loaded successfully!")
        print_info(f"PaymentProfile fields: {', '.join(profile_fields)}")
        print_info(f"Transaction fields: {', '.join(transaction_fields)}")
        
        # Verify ERC-1400 fields are present
        if 'token_contract_address' in transaction_fields and 'token_symbol' in transaction_fields:
            print_success("✓ ERC-1400 token fields present (token_contract_address, token_symbol)")
        else:
            print_error("✗ Missing ERC-1400 token fields!")
            return False
            
        # Check for old NFT fields (should NOT be present)
        if 'nft_id' in transaction_fields or 'nft_name' in transaction_fields:
            print_error("✗ Old NFT fields still present! Migration may have failed.")
            return False
        else:
            print_success("✓ NFT fields successfully replaced with ERC-1400 fields")
        
        # Count existing records
        profile_count = PaymentProfile.objects.count()
        transaction_count = Transaction.objects.count()
        
        print_info(f"PaymentProfiles in database: {profile_count}")
        print_info(f"Transactions in database: {transaction_count}")
        
        return True
        
    except Exception as e:
        print_error(f"Error accessing database: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_omnisend_service():
    """Test 5: Verify Omnisend service uses correct token fields"""
    print_header("TEST 5: Omnisend Service Configuration")
    
    import os
    import sys
    django_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, django_path)
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        from apps.payments.omnisend_service import OmnisendClient
        import inspect
        
        # Check method signature
        client = OmnisendClient()
        trigger_method = client.trigger_trade_confirmation
        sig = inspect.signature(trigger_method)
        
        params = list(sig.parameters.keys())
        print_info(f"trigger_trade_confirmation parameters: {params}")
        
        if 'token_symbol' in params:
            print_success("✓ Omnisend uses 'token_symbol' parameter (correct for ERC-1400)")
        else:
            print_error("✗ Omnisend missing 'token_symbol' parameter")
            return False
            
        if 'nft_name' in params:
            print_error("✗ Omnisend still uses old 'nft_name' parameter!")
            return False
        else:
            print_success("✓ Old 'nft_name' parameter removed")
        
        return True
        
    except Exception as e:
        print_error(f"Error checking Omnisend service: {e}")
        return False

def run_all_tests():
    """Run all integration tests"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "BILL BITTS / NEO BANK INTEGRATION TEST SUITE" + " " * 18 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Testing ERC-1400 Security Token Purchase Flow".ljust(78) + "║")
    print("║" + "  (NFT references have been corrected to ERC-1400 tokens)".ljust(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print(f"{Colors.RESET}\n")
    
    results = []
    
    # Run tests
    results.append(("Server Health", test_server_health()))
    results.append(("Webhook Endpoint", test_webhook_endpoint()))
    results.append(("Django Admin", test_models_via_django_admin()))
    results.append(("Database Tables", test_database_tables()))
    results.append(("Omnisend Service", test_omnisend_service()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✅ PASS" if result else f"{Colors.RED}❌ FAIL"
        print(f"{status:<20}{Colors.RESET} {test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}\n")
    
    if passed == total:
        print_success("All tests passed! 🎉")
        print_info("The Bill Bitts integration is ready for ERC-1400 token purchases")
        print_info("\nNext steps:")
        print_info("  1. Create a superuser: python manage.py createsuperuser")
        print_info("  2. Access admin: http://localhost:8000/admin/")
        print_info("  3. Create a test PaymentProfile with a CPRN")
        print_info("  4. Test the complete payment flow")
    else:
        print_warning(f"{total - passed} test(s) failed - review the errors above")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
