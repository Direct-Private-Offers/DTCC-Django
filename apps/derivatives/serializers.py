from rest_framework import serializers


class DerivativeRequestSerializer(serializers.Serializer):
    isin = serializers.RegexField(r'^[A-Z]{2}[A-Z0-9]{9}\d$', max_length=12)
    uti = serializers.CharField(max_length=64, required=False, allow_blank=True)
    priorUti = serializers.CharField(max_length=64, required=False, allow_blank=True)
    upi = serializers.CharField(max_length=64)
    effectiveDate = serializers.DateField()
    expirationDate = serializers.DateField(required=False, allow_null=True)
    executionTimestamp = serializers.DateTimeField()
    notionalAmount = serializers.DecimalField(max_digits=36, decimal_places=6)
    notionalCurrency = serializers.CharField(max_length=8)
    productType = serializers.CharField(max_length=32)
    underlyingAsset = serializers.CharField(max_length=64)
    counterpartyLei = serializers.CharField(max_length=32, required=False, allow_blank=True)
    reportingEntityLei = serializers.CharField(max_length=32, required=False, allow_blank=True)
    action = serializers.ChoiceField(['NEW', 'AMEND', 'CORRECT', 'CANCEL'])
