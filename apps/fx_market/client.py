import os
import httpx
import logging
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class FxMarketClient:
    """
    FX-to-Market API client for FX conversion and cross-platform settlement.
    """
    
    def __init__(self):
        self.base = os.getenv('FX_MARKET_API_BASE', 'https://api.fxmarket.example/v1')
        self.key = os.getenv('FX_MARKET_API_KEY', '')
        self.timeout = int(os.getenv('FX_MARKET_TIMEOUT', '30'))
        
    def _headers(self) -> Dict[str, str]:
        """Generate request headers with authentication"""
        return {
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
        }
    
    def convert_fx_to_token(
        self,
        amount: float,
        currency: str,
        token_address: str,
        user_id: str
    ) -> Optional[Dict]:
        """
        Convert FX (fiat) to security token.
        
        Args:
            amount: Amount in fiat currency
            currency: Fiat currency code (USD, EUR, etc.)
            token_address: Security token contract address
            user_id: User identifier
            
        Returns:
            Conversion result dict with token amount and transaction ID
        """
        try:
            payload = {
                'amount': amount,
                'currency': currency,
                'token_address': token_address,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
            }
            
            response = httpx.post(
                f"{self.base}/convert/fx-to-token",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error converting FX to token: {e.response.status_code}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock FX-to-token conversion: {amount} {currency}")
                return {
                    'converted': True,
                    'token_amount': str(amount * 0.001),  # Mock conversion rate
                    'transaction_id': f'FX-TX-{datetime.now().timestamp()}'
                }
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error converting FX to token: {str(e)}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock FX-to-token conversion: {amount} {currency}")
                return {
                    'converted': True,
                    'token_amount': str(amount * 0.001),
                    'transaction_id': f'FX-TX-{datetime.now().timestamp()}'
                }
            return None
        except Exception as e:
            logger.error(f"Error converting FX to token: {str(e)}")
            return None
    
    def convert_token_to_fx(
        self,
        token_amount: float,
        token_address: str,
        target_currency: str,
        user_id: str
    ) -> Optional[Dict]:
        """
        Convert security token to FX (fiat).
        
        Args:
            token_amount: Amount of tokens
            token_address: Security token contract address
            target_currency: Target fiat currency code
            user_id: User identifier
            
        Returns:
            Conversion result dict with fiat amount and transaction ID
        """
        try:
            payload = {
                'token_amount': token_amount,
                'token_address': token_address,
                'target_currency': target_currency,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
            }
            
            response = httpx.post(
                f"{self.base}/convert/token-to-fx",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error converting token to FX: {e.response.status_code}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock token-to-FX conversion: {token_amount} tokens")
                return {
                    'converted': True,
                    'fiat_amount': str(token_amount * 1000),  # Mock conversion rate
                    'currency': target_currency,
                    'transaction_id': f'FX-TX-{datetime.now().timestamp()}'
                }
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error converting token to FX: {str(e)}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock token-to-FX conversion: {token_amount} tokens")
                return {
                    'converted': True,
                    'fiat_amount': str(token_amount * 1000),
                    'currency': target_currency,
                    'transaction_id': f'FX-TX-{datetime.now().timestamp()}'
                }
            return None
        except Exception as e:
            logger.error(f"Error converting token to FX: {str(e)}")
            return None
    
    def initiate_cross_platform_settlement(
        self,
        settlement_id: str,
        settlement_data: Dict
    ) -> Optional[Dict]:
        """
        Initiate cross-platform settlement on FX-to-market.
        
        Args:
            settlement_id: Settlement identifier
            settlement_data: Settlement data dictionary
            
        Returns:
            Settlement initiation confirmation dict
        """
        try:
            payload = {
                'settlement_id': settlement_id,
                'settlement_data': settlement_data,
                'timestamp': datetime.now().isoformat(),
            }
            
            response = httpx.post(
                f"{self.base}/settlements/initiate",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error initiating cross-platform settlement: {e.response.status_code}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock settlement initiation: {settlement_id}")
                return {
                    'initiated': True,
                    'settlement_id': settlement_id,
                    'fx_settlement_id': f'FX-SETTLE-{settlement_id}'
                }
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error initiating cross-platform settlement: {str(e)}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock settlement initiation: {settlement_id}")
                return {
                    'initiated': True,
                    'settlement_id': settlement_id,
                    'fx_settlement_id': f'FX-SETTLE-{settlement_id}'
                }
            return None
        except Exception as e:
            logger.error(f"Error initiating cross-platform settlement: {str(e)}")
            return None
    
    def get_settlement_status(
        self,
        settlement_id: str
    ) -> Optional[Dict]:
        """
        Get settlement status from FX-to-market.
        
        Args:
            settlement_id: Settlement identifier
            
        Returns:
            Settlement status dict
        """
        try:
            response = httpx.get(
                f"{self.base}/settlements/{settlement_id}",
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting settlement status from FX-to-market: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error getting settlement status from FX-to-market: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting settlement status from FX-to-market: {str(e)}")
            return None
    
    def transfer_token(
        self,
        from_user_id: str,
        to_user_id: str,
        token_address: str,
        amount: float
    ) -> Optional[Dict]:
        """
        Transfer token between DPO and FX-to-market platforms.
        
        Args:
            from_user_id: Source user identifier
            to_user_id: Destination user identifier
            token_address: Token contract address
            amount: Token amount
            
        Returns:
            Transfer confirmation dict
        """
        try:
            payload = {
                'from_user_id': from_user_id,
                'to_user_id': to_user_id,
                'token_address': token_address,
                'amount': amount,
                'timestamp': datetime.now().isoformat(),
            }
            
            response = httpx.post(
                f"{self.base}/tokens/transfer",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error transferring token: {e.response.status_code}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock token transfer: {amount} from {from_user_id} to {to_user_id}")
                return {
                    'transferred': True,
                    'transaction_id': f'FX-TRANSFER-{datetime.now().timestamp()}'
                }
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error transferring token: {str(e)}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock token transfer: {amount} from {from_user_id} to {to_user_id}")
                return {
                    'transferred': True,
                    'transaction_id': f'FX-TRANSFER-{datetime.now().timestamp()}'
                }
            return None
        except Exception as e:
            logger.error(f"Error transferring token: {str(e)}")
            return None

