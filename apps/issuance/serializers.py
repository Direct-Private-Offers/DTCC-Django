from rest_framework import serializers
import re


class IssuanceRequestSerializer(serializers.Serializer):
    isin = serializers.RegexField(r'^[A-Z]{2}[A-Z0-9]{9}\d$', max_length=12)
    investorAddress = serializers.CharField(max_length=128)
    amount = serializers.DecimalField(max_digits=36, decimal_places=18)
    euroclearRef = serializers.CharField(max_length=128, required=False, allow_blank=True)
    ipfsCID = serializers.CharField(max_length=128, required=False, allow_blank=True)
    offeringType = serializers.ChoiceField(['RegD', 'RegCF', '144A'], required=False)
    metadata = serializers.JSONField(required=False)
    
    def validate_investorAddress(self, value):
        """Validate Ethereum address format (0x followed by 40 hex characters)"""
        if not value:
            return value
        # Basic Ethereum address validation
        if not re.match(r'^0x[a-fA-F0-9]{40}$', value):
            raise serializers.ValidationError("Invalid Ethereum address format. Must be 0x followed by 40 hex characters.")
        return value
