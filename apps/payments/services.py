"""
Bill Bitts API Client
Handles RSA-2048 signed requests to Bill Bitts payment gateway
"""
import requests
import json
import base64
import logging
from pathlib import Path
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from django.conf import settings

logger = logging.getLogger(__name__)


class BillBittsClient:
    """
    Client for Bill Bitts API with RSA-2048 signature authentication
    """
    
    def __init__(self, private_key_path=None, api_url=None):
        self.api_url = api_url or getattr(settings, 'BILLBITTS_API_URL', 'https://api.billbitcoins.com')
        
        # Load private key
        key_path = private_key_path or getattr(settings, 'BILLBITTS_PRIVATE_KEY_PATH', None)
        if key_path and Path(key_path).exists():
            with open(key_path, 'r') as f:
                self.private_key = RSA.import_key(f.read())
        else:
            logger.warning("Bill Bitts private key not found. Signature authentication disabled.")
            self.private_key = None
    
    def sign_payload(self, data: dict) -> str:
        """
        Signs the JSON payload using RSA 2048-bit (SHA256).
        
        Args:
            data: Dictionary to be signed
            
        Returns:
            Base64-encoded signature string
        """
        if not self.private_key:
            raise ValueError("Private key not loaded. Cannot sign payload.")
        
        payload_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        h = SHA256.new(payload_bytes)
        signature = pkcs1_15.new(self.private_key).sign(h)
        return base64.b64encode(signature).decode('utf-8')
    
    def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """
        Makes an authenticated request to Bill Bitts API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request payload
            
        Returns:
            Response JSON
        """
        url = f"{self.api_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Sign the payload if POST/PUT
        if data and self.private_key:
            signature = self.sign_payload(data)
            headers['X-Signature'] = signature
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Bill Bitts API error: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def create_registration(self, user_data: dict) -> dict:
        """
        Registers a user to generate a CPRN (Customer Presentment Registration Number)
        
        Args:
            user_data: Dictionary containing user information
                {
                    'email': 'user@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'phone': '+1234567890'
                }
        
        Returns:
            Response with CPRN: {'cprn': 'CPRN-XXXXXXXX', 'status': 'success'}
        """
        return self._make_request('POST', '/register', user_data)
    
    def initiate_payment(self, payment_data: dict) -> dict:
        """
        Initiates a payment transaction
        
        Args:
            payment_data: Payment details
                {
                    'cprn': 'CPRN-XXXXXXXX',
                    'amount': '100.00',
                    'currency': 'USD',
                    'description': 'ERC-1400 Security Token Purchase'
                }
        
        Returns:
            Transaction response with tx_id
        """
        return self._make_request('POST', '/payment/initiate', payment_data)
    
    def check_balance(self, cprn: str) -> dict:
        """
        Checks the balance for a given CPRN
        
        Args:
            cprn: Customer Presentment Registration Number
            
        Returns:
            Balance information
        """
        return self._make_request('GET', f'/balance/{cprn}')
