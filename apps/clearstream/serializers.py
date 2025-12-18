from rest_framework import serializers


class AccountCreateSerializer(serializers.Serializer):
    csd_participant = serializers.CharField(max_length=64)
    csd_account = serializers.CharField(max_length=64)
    lei = serializers.CharField(max_length=32, required=False, allow_blank=True)
    permissions = serializers.ListField(child=serializers.CharField(), required=False)


class InstructionCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(['DELIVERY', 'RECEIPT'])
    isin = serializers.RegexField(r'^[A-Z]{2}[A-Z0-9]{9}\d$', max_length=12)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=18)
    counterparty = serializers.CharField(max_length=128)
    settlementDate = serializers.DateField(required=False)
    priority = serializers.IntegerField(required=False)
    partialAllowed = serializers.BooleanField(required=False)


class ClearstreamSettlementCreateSerializer(serializers.Serializer):
    isin = serializers.RegexField(r'^[A-Z]{2}[A-Z0-9]{9}\d$', max_length=12)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=18)
    account = serializers.CharField(max_length=128, required=False, allow_blank=True)
    counterparty = serializers.CharField(max_length=128, required=False, allow_blank=True)
