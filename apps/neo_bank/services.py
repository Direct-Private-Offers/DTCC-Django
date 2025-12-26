import logging
from typing import Optional, Dict
from django.contrib.auth.models import User
from .client import NeoBankClient
from .models import NeoBankAccountLink, KycSyncStatus, TransactionSync

logger = logging.getLogger(__name__)


class NeoBankSyncService:
    """Service for synchronizing data with NEO bank"""
    
    def __init__(self):
        self.client = NeoBankClient()
    
    def sync_kyc(self, user: User, kyc_data: Dict) -> Optional[KycSyncStatus]:
        """
        Synchronize KYC data with NEO bank.
        
        Args:
            user: User instance
            kyc_data: KYC data dictionary
            
        Returns:
            KycSyncStatus instance
        """
        try:
            # Get existing sync status or create new
            sync_status, created = KycSyncStatus.objects.get_or_create(
                user=user,
                defaults={'dpo_kyc_data': kyc_data}
            )
            
            if not created:
                sync_status.dpo_kyc_data = kyc_data
            
            # Sync with NEO bank
            result = self.client.sync_kyc_status(str(user.id), kyc_data)
            
            if result:
                sync_status.neo_kyc_data = result.get('kyc_data', {})
                sync_status.sync_status = 'SYNCED'
                sync_status.save()
                return sync_status
            else:
                sync_status.sync_status = 'ERROR'
                sync_status.save()
                return None
        except Exception as e:
            logger.error(f"Error syncing KYC for user {user.id}: {str(e)}")
            return None
    
    def link_account(self, user: User, neo_account_id: str, permissions: Optional[list] = None) -> Optional[NeoBankAccountLink]:
        """
        Link DPO account with NEO bank account.
        
        Args:
            user: User instance
            neo_account_id: NEO bank account identifier
            permissions: List of permissions
            
        Returns:
            NeoBankAccountLink instance
        """
        try:
            result = self.client.link_account(str(user.id), neo_account_id, permissions)
            
            if result:
                link, created = NeoBankAccountLink.objects.update_or_create(
                    user=user,
                    defaults={
                        'neo_account_id': neo_account_id,
                        'permissions': permissions or [],
                        'is_active': True
                    }
                )
                return link
            return None
        except Exception as e:
            logger.error(f"Error linking account for user {user.id}: {str(e)}")
            return None
    
    def sync_transaction(self, user: User, transaction_id: str, transaction_data: Dict) -> Optional[TransactionSync]:
        """
        Synchronize transaction with NEO bank.
        
        Args:
            user: User instance
            transaction_id: Transaction identifier
            transaction_data: Transaction data dictionary
            
        Returns:
            TransactionSync instance
        """
        try:
            result = self.client.sync_transaction(transaction_id, transaction_data)
            
            if result:
                sync, created = TransactionSync.objects.update_or_create(
                    transaction_id=transaction_id,
                    defaults={
                        'user': user,
                        'sync_status': 'SYNCED',
                        'neo_transaction_id': result.get('neo_transaction_id')
                    }
                )
                return sync
            else:
                TransactionSync.objects.update_or_create(
                    transaction_id=transaction_id,
                    defaults={
                        'user': user,
                        'sync_status': 'ERROR'
                    }
                )
                return None
        except Exception as e:
            logger.error(f"Error syncing transaction {transaction_id}: {str(e)}")
            return None

