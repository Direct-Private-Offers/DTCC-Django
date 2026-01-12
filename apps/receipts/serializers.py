from rest_framework import serializers
from .models import Receipt


class ReceiptSerializer(serializers.ModelSerializer):
    investor_username = serializers.CharField(source='investor.username', read_only=True)
    pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Receipt
        fields = [
            'id', 'receipt_id', 'receipt_type', 'investor', 'investor_username',
            'transaction_id', 'isin', 'quantity', 'amount', 'currency',
            'pdf_url', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'receipt_id', 'created_at']
    
    def get_pdf_url(self, obj):
        """Get PDF file URL"""
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return None


class ReceiptCreateSerializer(serializers.Serializer):
    """Serializer for creating receipts"""
    receipt_type = serializers.ChoiceField(choices=['ISSUANCE', 'TRANSFER', 'SETTLEMENT'], required=True)
    transaction_id = serializers.UUIDField(required=True)
    isin = serializers.CharField(max_length=12, required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=18, required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=36, decimal_places=18, required=False, allow_null=True)
    currency = serializers.CharField(max_length=3, default='USD')
    metadata = serializers.JSONField(required=False, default=dict)
