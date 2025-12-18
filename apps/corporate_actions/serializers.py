from rest_framework import serializers


class CorporateActionCreateSerializer(serializers.Serializer):
    # Support both formats: simplified (current) and full (from TypeScript types)
    isin = serializers.RegexField(r'^[A-Z]{2}[A-Z0-9]{9}\d$', max_length=12)
    type = serializers.ChoiceField(['DIVIDEND', 'SPLIT', 'MERGER', 'RIGHTS_ISSUE'], required=False)
    actionType = serializers.ChoiceField(['DIVIDEND', 'SPLIT', 'MERGER', 'RIGHTS_ISSUE'], required=False)
    recordDate = serializers.DateField(required=False)
    effectiveDate = serializers.DateField(required=False)
    paymentDate = serializers.DateField(required=False, allow_null=True)
    reference = serializers.CharField(max_length=128, required=False, allow_blank=True)
    data = serializers.JSONField(required=False)
    factor = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    amountPerShare = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    currency = serializers.CharField(max_length=8, required=False, allow_blank=True)
    
    def validate(self, attrs):
        # Map actionType to type if needed (create a copy to avoid mutating input)
        data = attrs.copy()
        if data.get('actionType') and not data.get('type'):
            data['type'] = data['actionType']
        # Ensure type/actionType is provided
        if not data.get('type') and not data.get('actionType'):
            raise serializers.ValidationError("Either 'type' or 'actionType' must be provided")
        # Ensure recordDate is provided
        if not data.get('recordDate'):
            raise serializers.ValidationError("'recordDate' is required")
        # If using new format, ensure required fields
        if data.get('effectiveDate') or data.get('reference'):
            if not data.get('effectiveDate'):
                raise serializers.ValidationError("'effectiveDate' is required when using corporate action format with reference")
            if not data.get('reference'):
                raise serializers.ValidationError("'reference' is required when using corporate action format with reference")
            # Validate that effectiveDate >= recordDate
            if data.get('effectiveDate') and data.get('recordDate'):
                if data['effectiveDate'] < data['recordDate']:
                    raise serializers.ValidationError("'effectiveDate' cannot be before 'recordDate'")
        return data
