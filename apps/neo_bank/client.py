import os
import httpx
import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class NeoBankClient:
    """
    NEO Bank API client for KYC/AML synchronization and account linking.
    """
    
    def __init__(self):
        self.base = os.getenv('NEO_BANK_API_BASE', 'https://api.neobank.example/v1')
        self.key = os.getenv('NEO_BANK_API_KEY', '')
        self.timeout = int(os.getenv('NEO_BANK_TIMEOUT', '30'))
        
    def _headers(self) -> Dict[str, str]:
        """Generate request headers with authentication"""
        return {
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
        }
    
    def sync_kyc_status(
        self,
        user_id: str,
        kyc_data: Dict
    ) -> Optional[Dict]:
        """
        Synchronize KYC status with NEO bank.
        
        Args:
            user_id: User identifier
            kyc_data: KYC data dictionary
            
        Returns:
            Sync confirmation dict
        """
        try:
            payload = {
                'user_id': user_id,
                'kyc_data': kyc_data,
                'timestamp': datetime.now().isoformat(),
            }
            
            response = httpx.post(
                f"{self.base}/kyc/sync",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error syncing KYC with NEO bank: {e.response.status_code}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock KYC sync for user: {user_id}")
                return {'synced': True, 'user_id': user_id}
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error syncing KYC with NEO bank: {str(e)}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock KYC sync for user: {user_id}")
                return {'synced': True, 'user_id': user_id}
            return None
        except Exception as e:
            logger.error(f"Error syncing KYC with NEO bank: {str(e)}")
            return None
    
    def link_account(
        self,
        user_id: str,
        neo_account_id: str,
        permissions: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Link DPO account with NEO bank account.
        
        Args:
            user_id: DPO user identifier
            neo_account_id: NEO bank account identifier
            permissions: List of permissions (optional)
            
        Returns:
            Account linking confirmation dict
        """
        try:
            payload = {
                'user_id': user_id,
                'neo_account_id': neo_account_id,
            }
            
            if permissions:
                payload['permissions'] = permissions
            
            response = httpx.post(
                f"{self.base}/accounts/link",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error linking account with NEO bank: {e.response.status_code}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock account linking: {user_id} -> {neo_account_id}")
                return {'linked': True, 'user_id': user_id, 'neo_account_id': neo_account_id}
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error linking account with NEO bank: {str(e)}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock account linking: {user_id} -> {neo_account_id}")
                return {'linked': True, 'user_id': user_id, 'neo_account_id': neo_account_id}
            return None
        except Exception as e:
            logger.error(f"Error linking account with NEO bank: {str(e)}")
            return None
    
    def get_compliance_status(
        self,
        user_id: str
    ) -> Optional[Dict]:
        """
        Get compliance status from NEO bank.
        
        Args:
            user_id: User identifier
            
        Returns:
            Compliance status dict
        """
        try:
            response = httpx.get(
                f"{self.base}/compliance/{user_id}",
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting compliance status from NEO bank: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error getting compliance status from NEO bank: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting compliance status from NEO bank: {str(e)}")
            return None
    
    def sync_transaction(
        self,
        transaction_id: str,
        transaction_data: Dict
    ) -> Optional[Dict]:
        """
        Synchronize transaction with NEO bank for reconciliation.
        
        Args:
            transaction_id: Transaction identifier
            transaction_data: Transaction data dictionary
            
        Returns:
            Sync confirmation dict
        """
        try:
            payload = {
                'transaction_id': transaction_id,
                'transaction_data': transaction_data,
                'timestamp': datetime.now().isoformat(),
            }
            
            response = httpx.post(
                f"{self.base}/transactions/sync",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error syncing transaction with NEO bank: {e.response.status_code}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock transaction sync: {transaction_id}")
                return {'synced': True, 'transaction_id': transaction_id}
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error syncing transaction with NEO bank: {str(e)}")
            if self.base.endswith('.example'):
                logger.debug(f"Using mock transaction sync: {transaction_id}")
                return {'synced': True, 'transaction_id': transaction_id}
            return None
        except Exception as e:
            logger.error(f"Error syncing transaction with NEO bank: {str(e)}")
            return None

