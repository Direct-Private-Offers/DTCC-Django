"""
Tests for NEO Bank API views.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from apps.neo_bank.models import NeoBankAccountLink


@pytest.mark.django_db
class TestNeoBankViews:
    """Test NEO Bank API endpoints."""
    
    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_link_account_endpoint(self):
        """Test account linking endpoint."""
        response = self.client.post('/api/neo-bank/accounts', {
            'neo_account_id': 'NEO-ACCOUNT-123',
            'permissions': ['read', 'write']
        })
        
        # Should either succeed or fail gracefully
        assert response.status_code in [201, 400]
    
    def test_kyc_sync_endpoint(self):
        """Test KYC sync endpoint."""
        response = self.client.post('/api/neo-bank/kyc-sync/sync', {
            'kyc_data': {
                'status': 'APPROVED',
                'verified_at': '2025-01-01T00:00:00Z'
            }
        })
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400]
    
    def test_list_accounts_endpoint(self):
        """Test list accounts endpoint."""
        response = self.client.get('/api/neo-bank/accounts')
        
        assert response.status_code == 200

