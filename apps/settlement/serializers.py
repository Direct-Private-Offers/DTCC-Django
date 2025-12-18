from rest_framework import serializers
import re


class SettlementCreateSerializer(serializers.Serializer):
    # Support both formats: simplified (current) and full (from TypeScript types)
    isin = serializers.RegexField(r'^[A-Z]{2}[A-Z0-9]{9}\d$', max_length=12)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=18, required=False)
    amount = serializers.DecimalField(max_digits=36, decimal_places=18, required=False)
    tradeRef = serializers.CharField(max_length=128, required=False, allow_blank=True)
    fromAddress = serializers.CharField(max_length=128, required=False, allow_blank=True)
    toAddress = serializers.CharField(max_length=128, required=False, allow_blank=True)
    euroclearRef = serializers.CharField(max_length=128, required=False, allow_blank=True)
    tradeDate = serializers.DateField(required=False)
    valueDate = serializers.DateField(required=False)
    counterparty = serializers.CharField(max_length=128, required=False, allow_blank=True)
    account = serializers.CharField(max_length=128, required=False, allow_blank=True)
    
    def validate(self, data):
        # Ensure either quantity or amount is provided
        if not data.get('quantity') and not data.get('amount'):
            raise serializers.ValidationError("Either 'quantity' or 'amount' must be provided")
        # If using new format (with tradeRef/addresses), ensure all required fields
        if data.get('tradeRef') or data.get('fromAddress') or data.get('toAddress'):
            if not data.get('tradeRef'):
                raise serializers.ValidationError("'tradeRef' is required when using settlement format with addresses")
            if not data.get('fromAddress'):
                raise serializers.ValidationError("'fromAddress' is required when using settlement format with addresses")
            if not data.get('toAddress'):
                raise serializers.ValidationError("'toAddress' is required when using settlement format with addresses")
            if not data.get('amount'):
                raise serializers.ValidationError("'amount' is required when using settlement format with addresses")
            if not data.get('euroclearRef'):
                raise serializers.ValidationError("'euroclearRef' is required when using settlement format with addresses")
            # Validate Ethereum addresses if provided
            if data.get('fromAddress') and not re.match(r'^0x[a-fA-F0-9]{40}$', data['fromAddress']):
                raise serializers.ValidationError("'fromAddress' must be a valid Ethereum address")
            if data.get('toAddress') and not re.match(r'^0x[a-fA-F0-9]{40}$', data['toAddress']):
                raise serializers.ValidationError("'toAddress' must be a valid Ethereum address")
        return data
