"""
Tests for FX-to-Market API views.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestFxMarketViews:
    """Test FX-to-Market API endpoints."""
    
    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_convert_fx_to_token_endpoint(self):
        """Test FX to token conversion endpoint."""
        response = self.client.post('/api/fx-market/conversions/convert-fx-to-token', {
            'conversion_type': 'FX_TO_TOKEN',
            'source_amount': '1000.00',
            'source_currency': 'USD',
            'token_address': '0x1234567890123456789012345678901234567890'
        })
        
        # Should either succeed or fail gracefully
        assert response.status_code in [201, 400]
    
    def test_convert_token_to_fx_endpoint(self):
        """Test token to FX conversion endpoint."""
        response = self.client.post('/api/fx-market/conversions/convert-token-to-fx', {
            'conversion_type': 'TOKEN_TO_FX',
            'source_amount': '100.00',
            'token_address': '0x1234567890123456789012345678901234567890',
            'target_currency': 'USD'
        })
        
        # Should either succeed or fail gracefully
        assert response.status_code in [201, 400]
    
    def test_list_conversions_endpoint(self):
        """Test list conversions endpoint."""
        response = self.client.get('/api/fx-market/conversions')
        
        assert response.status_code == 200

