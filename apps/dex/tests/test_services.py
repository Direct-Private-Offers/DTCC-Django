"""
Tests for DEX services.
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from apps.dex.models import Wallet, Order
from apps.dex.services import create_order, match_orders, cancel_order, get_order_book


class TestDEXServices:
    """Test DEX service functions."""
    
    @pytest.fixture
    def test_wallet(self, test_user):
        """Create a test wallet."""
        return Wallet.objects.create(
            user=test_user,
            address='0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
            network='BSC'
        )
    
    def test_create_order(self, test_wallet):
        """Test order creation."""
        order_data = {
            'order_type': Order.OrderType.BUY,
            'isin': 'US0378331005',
            'quantity': Decimal('100'),
            'price_per_unit': Decimal('10.50'),
            'payment_token': 'USDC',
        }
        order = create_order(test_wallet, order_data)
        
        assert order.wallet == test_wallet
        assert order.order_type == Order.OrderType.BUY
        assert order.isin == 'US0378331005'
        assert order.quantity == Decimal('100')
        assert order.status == Order.OrderStatus.PENDING
    
    def test_cancel_order(self, test_wallet):
        """Test order cancellation."""
        order = Order.objects.create(
            wallet=test_wallet,
            order_type=Order.OrderType.BUY,
            isin='US0378331005',
            quantity=Decimal('100'),
            price_per_unit=Decimal('10.50'),
            status=Order.OrderStatus.PENDING
        )
        
        result = cancel_order(order)
        assert result is True
        order.refresh_from_db()
        assert order.status == Order.OrderStatus.CANCELLED
    
    def test_cancel_filled_order_fails(self, test_wallet):
        """Test that filled orders cannot be cancelled."""
        order = Order.objects.create(
            wallet=test_wallet,
            order_type=Order.OrderType.BUY,
            isin='US0378331005',
            quantity=Decimal('100'),
            price_per_unit=Decimal('10.50'),
            status=Order.OrderStatus.FILLED
        )
        
        result = cancel_order(order)
        assert result is False
    
    def test_get_order_book(self, test_wallet):
        """Test order book retrieval."""
        # Create some orders
        Order.objects.create(
            wallet=test_wallet,
            order_type=Order.OrderType.BUY,
            isin='US0378331005',
            quantity=Decimal('100'),
            price_per_unit=Decimal('10.00'),
            status=Order.OrderStatus.PENDING
        )
        
        Order.objects.create(
            wallet=test_wallet,
            order_type=Order.OrderType.SELL,
            isin='US0378331005',
            quantity=Decimal('50'),
            price_per_unit=Decimal('11.00'),
            status=Order.OrderStatus.PENDING
        )
        
        order_book = get_order_book('US0378331005')
        
        assert order_book['isin'] == 'US0378331005'
        assert len(order_book['buy_orders']) > 0
        assert len(order_book['sell_orders']) > 0

