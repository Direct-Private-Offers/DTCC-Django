"""
Tests for NEO Bank sync services.
"""
import pytest
from django.contrib.auth.models import User
from apps.neo_bank.services import NeoBankSyncService
from apps.neo_bank.models import NeoBankAccountLink, KycSyncStatus, TransactionSync
from decimal import Decimal


@pytest.mark.django_db
class TestNeoBankSyncService:
    """Test NEO Bank synchronization service."""
    
    def test_sync_kyc_creates_sync_status(self):
        """Test that syncing KYC creates a sync status record."""
        user = User.objects.create_user(username='testuser', email='test@example.com')
        service = NeoBankSyncService()
        
        kyc_data = {
            'status': 'APPROVED',
            'verified_at': '2025-01-01T00:00:00Z',
            'country': 'US'
        }
        
        sync_status = service.sync_kyc(user, kyc_data)
        
        assert sync_status is not None
        assert sync_status.user == user
        assert sync_status.dpo_kyc_data == kyc_data
        assert sync_status.sync_status in ['SYNCED', 'ERROR']
    
    def test_link_account_creates_link(self):
        """Test that linking account creates a link record."""
        user = User.objects.create_user(username='testuser', email='test@example.com')
        service = NeoBankSyncService()
        
        link = service.link_account(user, 'NEO-ACCOUNT-123', ['read', 'write'])
        
        assert link is not None
        assert link.user == user
        assert link.neo_account_id == 'NEO-ACCOUNT-123'
        assert link.is_active is True
    
    def test_sync_transaction_creates_record(self):
        """Test that syncing transaction creates a transaction sync record."""
        user = User.objects.create_user(username='testuser', email='test@example.com')
        service = NeoBankSyncService()
        
        import uuid
        transaction_id = str(uuid.uuid4())
        transaction_data = {
            'amount': '1000.00',
            'currency': 'USD',
            'type': 'DEPOSIT'
        }
        
        sync = service.sync_transaction(user, transaction_id, transaction_data)
        
        assert sync is not None
        assert sync.user == user
        assert sync.transaction_id == transaction_id
        assert sync.sync_status in ['SYNCED', 'ERROR']

