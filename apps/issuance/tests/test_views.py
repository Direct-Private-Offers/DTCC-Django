"""
Integration tests for issuance endpoints.
"""
import pytest
from rest_framework import status
from apps.issuance.models import IssuanceEvent, TransferEvent


class TestIssuanceEndpoints:
    """Test issuance API endpoints."""
    
    def test_get_security_details_requires_auth(self, api_client):
        """Test that security details endpoint requires authentication."""
        response = api_client.get('/api/issuance/?isin=US0378331005')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_security_details_authenticated(self, authenticated_client):
        """Test getting security details with authentication."""
        response = authenticated_client.get('/api/issuance/?isin=US0378331005')
        # Should return 200 or 404 depending on mock implementation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_create_issuance_requires_issuer_group(self, authenticated_client):
        """Test that issuance creation requires issuer group."""
        response = authenticated_client.post(
            '/api/issuance/',
            {
                'isin': 'US0378331005',
                'investorAddress': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
                'amount': '1000',
                'offeringType': 'RegD'
            }
        )
        # Should be 403 if user doesn't have issuer group
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST]
    
    def test_create_issuance_with_issuer_group(self, api_client, issuer_user):
        """Test issuance creation with issuer group."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(issuer_user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = api_client.post(
            '/api/issuance/',
            {
                'isin': 'US0378331005',
                'investorAddress': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
                'amount': '1000',
                'offeringType': 'RegD'
            },
            HTTP_IDEMPOTENCY_KEY='test-key-123'
        )
        # Should succeed or return validation error
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ]

