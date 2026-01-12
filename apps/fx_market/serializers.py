from rest_framework import serializers
from .models import FxConversion, CrossPlatformSettlement, TokenFlow


class FxConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FxConversion
        fields = [
            'id', 'conversion_type', 'status', 'source_amount', 'source_currency',
            'target_amount', 'target_currency', 'token_address', 'conversion_rate',
            'fee', 'fx_transaction_id', 'blockchain_tx_hash', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']


class FxConversionRequestSerializer(serializers.Serializer):
    """Serializer for FX conversion requests"""
    conversion_type = serializers.ChoiceField(choices=['FX_TO_TOKEN', 'TOKEN_TO_FX'])
    source_amount = serializers.DecimalField(max_digits=36, decimal_places=18)
    source_currency = serializers.CharField(max_length=3)
    token_address = serializers.CharField(max_length=42, required=False)
    target_currency = serializers.CharField(max_length=3, required=False)


class CrossPlatformSettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrossPlatformSettlement
        fields = [
            'id', 'dpo_settlement_id', 'fx_settlement_id', 'status', 'isin',
            'quantity', 'amount', 'currency', 'dpo_status', 'fx_status',
            'reconciled', 'reconciled_at', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class TokenFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenFlow
        fields = [
            'id', 'flow_direction', 'status', 'token_address', 'amount',
            'blockchain_tx_hash', 'fx_transaction_id', 'dpo_balance_before',
            'dpo_balance_after', 'fx_balance_before', 'fx_balance_after',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']

