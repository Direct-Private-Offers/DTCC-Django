import os
import httpx
import logging

logger = logging.getLogger(__name__)


class EuroclearClient:
    def __init__(self):
        self.base = os.getenv('EUROCLEAR_API_BASE', 'https://sandbox.euroclear.example/api')
        self.key = os.getenv('EUROCLEAR_API_KEY', 'test-key')
        self.timeout = int(os.getenv('EUROCLEAR_TIMEOUT', '30'))

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json'
        }

    def get_security_details(self, isin: str):
        """
        Get security details from Euroclear API.
        Returns None if security not found or on error.
        """
        if not isin:
            logger.warning("get_security_details called with empty ISIN")
            return None
        
        try:
            # Production implementation: call Euroclear API
            response = httpx.get(
                f"{self.base}/securities/{isin}",
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Security not found in Euroclear: {isin}")
                return None
            logger.error(f"HTTP error fetching security details for ISIN {isin}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching security details for ISIN {isin}: {str(e)}")
            # Fallback to mock in development if API is not available
            if self.base.endswith('.example'):
                logger.debug(f"Using mock data for ISIN: {isin}")
                return {'isin': isin, 'name': 'Mock Security', 'currency': 'USD'}
            return None
        except Exception as e:
            logger.error(f"Error fetching security details for ISIN {isin}: {str(e)}")
            return None

    def validate_investor(self, isin: str, address: str) -> bool:
        """
        Validate investor eligibility for a security.
        Returns False on error or if investor is not eligible.
        """
        if not isin or not address:
            logger.warning(f"validate_investor called with invalid parameters: isin={isin}, address={address}")
            return False
        
        try:
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
            return False
        except Exception as e:
            logger.error(f"Error validating investor {address} for ISIN {isin}: {str(e)}")
            return False

    def initiate_tokenization(self, payload: dict) -> str:
        """
        Initiate tokenization process with Euroclear.
        Returns transaction ID on success, raises exception on error.
        """
        try:
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
            raise Exception(f"Euroclear API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error initiating tokenization: {str(e)}")
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
