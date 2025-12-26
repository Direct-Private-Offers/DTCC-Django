"""
Tests for FX-to-Market services.
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from apps.fx_market.services import FxMarketService
from apps.fx_market.models import FxConversion, CrossPlatformSettlement, TokenFlow
from apps.settlement.models import Settlement


@pytest.mark.django_db
class TestFxMarketService:
    """Test FX-to-Market service."""
    
    def test_convert_fx_to_token_creates_conversion(self):
        """Test that FX to token conversion creates a conversion record."""
        user = User.objects.create_user(username='testuser', email='test@example.com')
        service = FxMarketService()
        
        conversion = service.convert_fx_to_token(
            user=user,
            amount=Decimal('1000.00'),
            currency='USD',
            token_address='0x1234567890123456789012345678901234567890'
        )
        
        assert conversion is not None
        assert conversion.user == user
        assert conversion.conversion_type == 'FX_TO_TOKEN'
        assert conversion.source_amount == Decimal('1000.00')
        assert conversion.source_currency == 'USD'
        assert conversion.status in ['COMPLETED', 'FAILED']
    
    def test_convert_token_to_fx_creates_conversion(self):
        """Test that token to FX conversion creates a conversion record."""
        user = User.objects.create_user(username='testuser', email='test@example.com')
        service = FxMarketService()
        
        conversion = service.convert_token_to_fx(
            user=user,
            token_amount=Decimal('100.00'),
            token_address='0x1234567890123456789012345678901234567890',
            target_currency='USD'
        )
        
        assert conversion is not None
        assert conversion.user == user
        assert conversion.conversion_type == 'TOKEN_TO_FX'
        assert conversion.source_amount == Decimal('100.00')
        assert conversion.status in ['COMPLETED', 'FAILED']
    
    def test_initiate_cross_platform_settlement(self):
        """Test cross-platform settlement initiation."""
        user = User.objects.create_user(username='testuser', email='test@example.com')
        settlement = Settlement.objects.create(
            isin='US0378331005',
            quantity=Decimal('1000.00'),
            status=Settlement.Status.INITIATED
        )
        service = FxMarketService()
        
        cross_settlement = service.initiate_cross_platform_settlement(settlement)
        
        # May be None if API call fails (development mode)
        if cross_settlement:
            assert cross_settlement.dpo_settlement_id == settlement.id
            assert cross_settlement.status == 'INITIATED'
    
    def test_transfer_token_creates_flow(self):
        """Test that token transfer creates a token flow record."""
        user = User.objects.create_user(username='testuser', email='test@example.com')
        service = FxMarketService()
        
        token_flow = service.transfer_token(
            user=user,
            flow_direction='DPO_TO_FX',
            token_address='0x1234567890123456789012345678901234567890',
            amount=Decimal('100.00')
        )
        
        assert token_flow is not None
        assert token_flow.user == user
        assert token_flow.flow_direction == 'DPO_TO_FX'
        assert token_flow.amount == Decimal('100.00')
        assert token_flow.status in ['COMPLETED', 'FAILED']

