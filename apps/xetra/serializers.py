from rest_framework import serializers
from .models import XetraTrade, XetraOrder, XetraSettlement, XetraPosition, XetraMarketData


class XetraTradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = XetraTrade
        fields = [
            'id', 'xetra_trade_id', 'isin', 'buyer_account', 'seller_account',
            'quantity', 'price', 'currency', 'trade_date', 'settlement_date',
            'status', 'xetra_reference', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class XetraOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = XetraOrder
        fields = [
            'id', 'xetra_order_id', 'isin', 'account', 'order_type', 'side',
            'quantity', 'price', 'status', 'filled_quantity', 'xetra_reference',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'filled_quantity', 'created_at', 'updated_at']


class XetraSettlementSerializer(serializers.ModelSerializer):
    trade = XetraTradeSerializer(read_only=True)
    
    class Meta:
        model = XetraSettlement
        fields = [
            'id', 'settlement_id', 'trade', 'isin', 'buyer_account', 'seller_account',
            'quantity', 'amount', 'currency', 'value_date', 'status',
            'xetra_instruction_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class XetraPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = XetraPosition
        fields = [
            'id', 'account', 'isin', 'settled_quantity', 'pending_quantity',
            'as_of', 'last_reconciled'
        ]
        read_only_fields = ['id']


class XetraMarketDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = XetraMarketData
        fields = [
            'id', 'isin', 'bid_price', 'ask_price', 'last_price', 'volume', 'timestamp'
        ]
        read_only_fields = ['id']


class XetraOrderCreateSerializer(serializers.Serializer):
    """Serializer for creating XETRA orders"""
    isin = serializers.CharField(max_length=12, required=True)
    account = serializers.CharField(max_length=64, required=True)
    order_type = serializers.ChoiceField(choices=['MARKET', 'LIMIT', 'STOP'], required=True)
    side = serializers.ChoiceField(choices=['BUY', 'SELL'], required=True)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=18, required=True)
    price = serializers.DecimalField(max_digits=36, decimal_places=18, required=False, allow_null=True)
    
    def validate(self, data):
        if data['order_type'] == 'LIMIT' and not data.get('price'):
            raise serializers.ValidationError("Price is required for LIMIT orders")
        return data
