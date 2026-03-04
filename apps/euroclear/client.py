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
        Fetch security details from Euroclear (or mock).
        Returns:
            - dict with security data on success
            - None if security not found (404)
            - dict with {"error": "..."} for API/connection failures
        """
        import time

        if not isin:
            logger.warning("get_security_details called with empty ISIN")
            return {"error": "empty_isin"}

        # -------------------------
        # MOCK MODE
        # -------------------------
        if self.mock_mode:
            logger.debug(f"[MOCK] Fetching security details for ISIN: {isin}")
            return {
                "isin": isin,
                "name": f"Mock Security {isin[:4]}",
                "currency": "USD",
                "issuer": "Mock Issuer Corp",
                "status": "active",
                "mock": True,
            }

        url = f"{self.base}/securities/{isin}"
        headers = self._headers()

        for attempt in range(2):  # simple retry
            try:
                t0 = time.time()
                logger.debug(f"[PROD] Fetching security details for ISIN {isin} (attempt {attempt+1})")

                response = httpx.get(url, headers=headers, timeout=self.timeout)
                latency = (time.time() - t0) * 1000

                response.raise_for_status()
                data = response.json()

                # Minimal schema validation
                if "isin" not in data or "name" not in data:
                    logger.error(f"Invalid schema from Euroclear for ISIN {isin}: {data}")
                    return {"error": "invalid_schema", "raw": data}

                logger.info(f"[PROD] Euroclear lookup OK for {isin} ({latency:.1f} ms)")
                return data

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Security not found in Euroclear: {isin}")
                    return None
                logger.error(
                    f"Euroclear HTTP error for ISIN {isin}: {e.response.status_code} "
                    f"(attempt {attempt+1})"
                )
                if attempt == 1:
                    return {"error": "http_error", "status": e.response.status_code}

            except httpx.RequestError as e:
                logger.error(f"Euroclear request error for ISIN {isin}: {str(e)} (attempt {attempt+1})")
                if attempt == 1:
                    return {"error": "request_error", "details": str(e)}

            except Exception as e:
                logger.error(f"Error fetching security details for ISIN {isin}: {str(e)}")
                if attempt == 1:
                    return {"error": "unknown_error", "details": str(e)}

        # Fallback to mock in development if API is not available
        if self.base.endswith('.example'):
            logger.debug(f"Using mock data for ISIN: {isin}")
            return {'isin': isin, 'name': 'Mock Security', 'currency': 'USD', 'mock': True}
        return {"error": "unreachable"}

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
            # PRODUCTION MODE - call Euroclear API
            response = httpx.get(
                f"{self.base}/validate/investor",
                params={'isin': isin, 'investorId': address},
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get('eligible', False)
            # Production implementation: call Euroclear API
            response = httpx.post(
                f"{self.base}/investors/validate",
                json={'isin': isin, 'address': address},
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get('eligible', False)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error validating investor {address} for ISIN {isin}: {e.response.status_code}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Request error validating investor {address} for ISIN {isin}: {str(e)}")
            # Fallback to mock in development if API is not available
            if self.base.endswith('.example'):
                logger.debug(f"Using mock validation for ISIN: {isin}, address: {address}")
                return bool(isin and address)
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
            response = httpx.post(
                f"{self.base}/tokenization/initiate",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            # Production implementation: call Euroclear API
            response = httpx.post(
                f"{self.base}/tokenization/initiate",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get('transactionId') or result.get('transaction_id')
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error initiating tokenization: {e.response.status_code}")
            raise Exception(f"Euroclear API error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error initiating tokenization: {str(e)}")
            # Fallback to mock in development if API is not available
            if self.base.endswith('.example'):
                isin = payload.get('isin') or 'UNKNOWN'
                logger.debug(f"Using mock tokenization for ISIN: {isin}")
                return 'TX-' + isin
        except Exception as e:
            logger.error(f"Error initiating tokenization for ISIN {isin}: {str(e)}")
            raise

    def report_derivative(self, payload: dict) -> str:
        """
        Report derivative trade to Euroclear.
        Returns UTI on success, raises exception on error.
        """
        try:
            # Production implementation: call Euroclear API
            response = httpx.post(
                f"{self.base}/derivatives/report",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get('uti') or result.get('unique_trade_id')
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error reporting derivative: {e.response.status_code}")
            raise Exception(f"Euroclear API error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error reporting derivative: {str(e)}")
            # Fallback to mock in development if API is not available
            if self.base.endswith('.example'):
                isin = payload.get('isin') or 'UNKNOWN'
                logger.debug(f"Using mock derivative reporting for ISIN: {isin}")
                return 'UTI-' + isin
            raise Exception(f"Euroclear API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error reporting derivative: {str(e)}")
            raise
