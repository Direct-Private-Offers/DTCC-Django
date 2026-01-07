import os
import httpx
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class EuroclearClient:
    """
    Euroclear API client with automatic mock mode.
    
    Mock Mode (default):
        - Activates when EUROCLEAR_API_KEY is empty, 'test-key', or starts with 'mock-'
        - Returns realistic fake data for all methods
        - Logs all calls for debugging
        
    Production Mode:
        - Activates when real API key is provided
        - Makes actual HTTP calls to Euroclear API
        - Requires valid credentials from Euroclear onboarding
    """
    
    def __init__(self):
        self.base = os.getenv('EUROCLEAR_API_BASE', 'https://sandbox.euroclear.example/api')
        self.key = os.getenv('EUROCLEAR_API_KEY', 'test-key')
        self.timeout = int(os.getenv('EUROCLEAR_TIMEOUT', '30'))
        self.mock_mode = self._is_mock_mode()
        
        if self.mock_mode:
            logger.info("Euroclear client initialized in MOCK MODE")
        else:
            logger.info(f"Euroclear client initialized in PRODUCTION MODE: {self.base}")

    def _is_mock_mode(self) -> bool:
        """Check if client should run in mock mode."""
        return (
            not self.key 
            or self.key == 'test-key' 
            or self.key.startswith('mock-')
            or 'sandbox.euroclear.example' in self.base
        )

    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json'
        }

    def get_security_details(self, isin: str) -> Optional[Dict[str, Any]]:
        """
        Get security details from Euroclear API.
        Returns None if security not found or on error.
        
        Args:
            isin: International Securities Identification Number
            
        Returns:
            Dict with security details or None on error
        """
        if not isin:
            logger.warning("get_security_details called with empty ISIN")
            return None
        
        try:
            if self.mock_mode:
                # MOCK MODE - return fake data
                logger.debug(f"[MOCK] Fetching security details for ISIN: {isin}")
                return {
                    'isin': isin,
                    'name': f'Mock Security {isin[:4]}',
                    'currency': 'USD',
                    'issuer': 'Mock Issuer Corp',
                    'status': 'active',
                    'mock': True,
                }
            else:
                # PRODUCTION MODE - real API call
                logger.debug(f"[PROD] Fetching security details for ISIN: {isin}")
                response = httpx.get(
                    f"{self.base}/securities/{isin}",
                    headers=self._headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching security details for ISIN {isin}: {str(e)}")
            return None

    def validate_investor(self, isin: str, address: str) -> bool:
        """
        Validate investor eligibility for a security.
        Returns False on error or if investor is not eligible.
        
        Args:
            isin: International Securities Identification Number
            address: Blockchain address or investor ID
            
        Returns:
            True if investor is eligible, False otherwise
        """
        if not isin or not address:
            logger.warning(f"validate_investor called with invalid parameters: isin={isin}, address={address}")
            return False
        
        try:
            if self.mock_mode:
                # MOCK MODE - always pass validation
                logger.debug(f"[MOCK] Validating investor {address} for ISIN: {isin}")
                return True
            else:
                # PRODUCTION MODE - call Euroclear API
                response = httpx.get(
                    f"{self.base}/validate/investor",
                    params={'isin': isin, 'investorId': address},
                    headers=self._headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json().get('eligible', False)
        except Exception as e:
            logger.error(f"Error validating investor {address} for ISIN {isin}: {str(e)}")
            return False

    def initiate_tokenization(self, payload: Dict[str, Any]) -> str:
        """
        Initiate tokenization process with Euroclear.
        
        Args:
            payload: Tokenization request payload with ISIN, amount, etc.
            
        Returns:
            Transaction ID string
            
        Raises:
            Exception on API error
        """
        try:
            isin = payload.get('isin') or 'UNKNOWN'
            
            if self.mock_mode:
                # MOCK MODE - return fake transaction ID
                logger.debug(f"[MOCK] Initiating tokenization for ISIN: {isin}")
                return f'MOCK-TX-{isin}-{hash(str(payload)) % 1000000:06d}'
            else:
                # PRODUCTION MODE - real API call
                logger.debug(f"[PROD] Initiating tokenization for ISIN: {isin}")
                response = httpx.post(
                    f"{self.base}/tokenization/initiate",
                    json=payload,
                    headers=self._headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json().get('transactionId')
        except Exception as e:
            logger.error(f"Error initiating tokenization for ISIN {isin}: {str(e)}")
            raise

    def report_derivative(self, payload: dict) -> str:
        """
        Report derivative trade to Euroclear.
        Returns UTI on success, raises exception on error.
        """
        try:
            # Stubbed: return a mock UTI
            # Example: response = httpx.post(f"{self.base}/derivatives/report", json=payload, headers=self._headers(), timeout=self.timeout)
            # response.raise_for_status()
            # return response.json().get('uti')
            isin = payload.get('isin') or 'UNKNOWN'
            logger.debug(f"Reporting derivative for ISIN: {isin}")
            return 'UTI-' + isin
        except Exception as e:
            logger.error(f"Error reporting derivative: {str(e)}")
            raise
