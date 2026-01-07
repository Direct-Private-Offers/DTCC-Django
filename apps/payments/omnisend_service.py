"""
Omnisend Marketing Automation Integration
Triggers email workflows based on payment events
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class OmnisendClient:
    """
    Client for Omnisend API to trigger marketing automation
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'OMNISEND_API_KEY', '')
        self.base_url = "https://api.omnisend.com/v3"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
    
    def trigger_event(self, event_name: str, email: str, properties: dict) -> bool:
        """
        Sends a custom event to Omnisend to trigger an Automation Workflow
        
        Args:
            event_name: Name of the event (must match Omnisend dashboard)
            email: User's email address
            properties: Dictionary of custom properties for the event
            
        Returns:
            True if successful, False otherwise
        """
        if not self.api_key:
            logger.warning("Omnisend API key not configured. Skipping event trigger.")
            return False
        
        endpoint = f"{self.base_url}/events"
        payload = {
            "eventName": event_name,
            "email": email,
            "properties": properties
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=10)
            if response.status_code == 202:
                logger.info(f"Omnisend event '{event_name}' triggered for {email}")
                return True
            else:
                logger.error(f"Omnisend API error: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Omnisend request failed: {e}")
            return False
    
    def trigger_trade_confirmation(self, email: str, amount: str, token_symbol: str) -> bool:
        """
        Triggers 'Security Token Trade Success' event
        
        Args:
            email: User's email
            amount: Transaction amount
            token_symbol: Symbol of the ERC-1400 security token traded
            
        Returns:
            True if successful
        """
        properties = {
            "trade_amount": str(amount),
            "token_symbol": token_symbol,
            "currency": "USD"
        }
        return self.trigger_event("Security Token Trade Success", email, properties)
    
    def trigger_registration_welcome(self, email: str, cprn: str) -> bool:
        """
        Triggers 'User Registration' welcome event
        
        Args:
            email: User's email
            cprn: Customer Presentment Registration Number
            
        Returns:
            True if successful
        """
        properties = {
            "cprn_number": cprn,
            "registration_date": "today"
        }
        return self.trigger_event("User Registration", email, properties)
    
    def trigger_payment_received(self, email: str, amount: str, transaction_id: str) -> bool:
        """
        Triggers 'Payment Received' event
        
        Args:
            email: User's email
            amount: Payment amount
            transaction_id: Transaction ID
            
        Returns:
            True if successful
        """
        properties = {
            "amount": str(amount),
            "transaction_id": transaction_id,
            "currency": "USD"
        }
        return self.trigger_event("Payment Received", email, properties)
