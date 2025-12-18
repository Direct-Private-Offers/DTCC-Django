from rest_framework import serializers
from .models import Wallet, Order, Swap, Trade
import re


class WalletCreateSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=128)
    network = serializers.CharField(max_length=32, default='BSC', required=False)
    
    def validate_address(self, value):
        """Validate Ethereum address format."""
        if not re.match(r'^0x[a-fA-F0-9]{40}$', value):
            raise serializers.ValidationError("Invalid Ethereum address format.")
        return value


class OrderCreateSerializer(serializers.Serializer):
    order_type = serializers.ChoiceField(choices=Order.OrderType.choices)
    isin = serializers.RegexField(r'^[A-Z]{2}[A-Z0-9]{9}\d$', max_length=12)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=18)
    price_per_unit = serializers.DecimalField(max_digits=36, decimal_places=18)
    payment_token = serializers.CharField(max_length=128, default='USDC', required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class OrderUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[Order.OrderStatus.CANCELLED], required=False)


class SwapCreateSerializer(serializers.Serializer):
    token_from = serializers.CharField(max_length=128)
    token_to = serializers.CharField(max_length=128)
    amount_from = serializers.DecimalField(max_digits=36, decimal_places=18)
    amount_to = serializers.DecimalField(max_digits=36, decimal_places=18)
    wallet_to_address = serializers.CharField(max_length=128, required=False, allow_blank=True)
    is_p2p = serializers.BooleanField(default=False, required=False)


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = ['id', 'isin', 'quantity', 'price_per_unit', 'total_value', 'tx_hash', 'created_at']


class OrderBookSerializer(serializers.Serializer):
    isin = serializers.CharField()
    buy_orders = serializers.ListField()
    sell_orders = serializers.ListField()

