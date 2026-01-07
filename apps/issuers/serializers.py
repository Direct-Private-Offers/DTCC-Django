"""
Issuer Serializers
Handles JSON serialization/deserialization for API endpoints.
Validates incoming data from BD forms against schema.
"""

from rest_framework import serializers
from .models import Issuer, IssuerDocument
from decimal import Decimal


class WireAccountSerializer(serializers.Serializer):
    """Nested serializer for wire transfer details"""
    bankName = serializers.CharField(max_length=255, required=False, allow_null=True)
    accountNumber = serializers.CharField(max_length=100, required=False, allow_null=True)
    routingNumber = serializers.CharField(max_length=100, required=False, allow_null=True)
    swift = serializers.CharField(max_length=11, required=False, allow_null=True)


class DocumentsSerializer(serializers.Serializer):
    """Nested serializer for offering documents"""
    prospectus = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    terms = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    risks = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    subscription = serializers.URLField(required=False, allow_null=True, allow_blank=True)


class IssuerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating issuers from BD form submissions.
    Matches BD_FORM_JSON_MAPPING.md structure.
    """
    
    # Nested objects
    wireAccount = WireAccountSerializer(required=False, allow_null=True)
    docs = DocumentsSerializer(required=False, allow_null=True)
    
    class Meta:
        model = Issuer
        fields = [
            # Basic Info
            'company_name',
            'logo',
            'security_name',
            'isin',
            
            # Offering Details
            'price_per_token',
            'total_offering',
            'min_investment',
            
            # Social Media
            'website',
            'linkedin',
            'twitter',
            'youtube',
            'facebook',
            'instagram',
            
            # Payment Rails
            'paypal_account',
            'wireAccount',
            'crypto_merchant_id',
            
            # Documents
            'docs',
            
            # Description
            'description',
            
            # SEC Form Data (optional)
            'sec_form_data',
            
            # BD Integration
            'bd_post_id',
        ]
        extra_kwargs = {
            'company_name': {'required': True},
            'security_name': {'required': True},
            'isin': {'required': True},
            'price_per_token': {'required': True},
            'total_offering': {'required': True},
            'min_investment': {'required': True},
        }
    
    def validate_isin(self, value):
        """Validate ISIN format (12 characters, alphanumeric)"""
        if not value or len(value) != 12:
            raise serializers.ValidationError("ISIN must be exactly 12 characters")
        if not value[:2].isalpha() or not value[2:].isalnum():
            raise serializers.ValidationError("Invalid ISIN format")
        return value.upper()
    
    def validate_price_per_token(self, value):
        """Ensure positive price"""
        if value <= 0:
            raise serializers.ValidationError("Price per token must be greater than 0")
        return value
    
    def create(self, validated_data):
        """
        Create issuer from BD form data.
        Handles nested objects (wireAccount, docs).
        """
        
        # Extract nested objects
        wire_account = validated_data.pop('wireAccount', None)
        docs = validated_data.pop('docs', None)
        
        # Create issuer instance
        issuer = Issuer(**validated_data)
        
        # Map wire account details
        if wire_account:
            issuer.wire_bank_name = wire_account.get('bankName')
            issuer.wire_account_number = wire_account.get('accountNumber')
            issuer.wire_routing_number = wire_account.get('routingNumber')
            issuer.wire_swift = wire_account.get('swift')
        
        # Map document URLs
        if docs:
            issuer.doc_prospectus = docs.get('prospectus')
            issuer.doc_terms = docs.get('terms')
            issuer.doc_risks = docs.get('risks')
            issuer.doc_subscription = docs.get('subscription')
        
        # Save issuer (triggers slug generation)
        issuer.save()
        
        return issuer


class IssuerResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for issuer API responses.
    Returns data formatted for offering template.
    """
    
    wireAccount = serializers.SerializerMethodField()
    docs = serializers.SerializerMethodField()
    
    class Meta:
        model = Issuer
        fields = [
            'id',
            'slug',
            'company_name',
            'logo',
            'security_name',
            'isin',
            'price_per_token',
            'total_offering',
            'min_investment',
            'website',
            'linkedin',
            'twitter',
            'youtube',
            'facebook',
            'instagram',
            'paypal_account',
            'wireAccount',
            'crypto_merchant_id',
            'docs',
            'description',
            'status',
            'offering_page_url',
            'created_at',
            'updated_at',
            'published_at',
        ]
        read_only_fields = ['id', 'slug', 'offering_page_url', 'created_at', 'updated_at']
    
    def get_wireAccount(self, obj):
        """Return wire account details as nested object"""
        return obj.wire_account_details
    
    def get_docs(self, obj):
        """Return document URLs as nested object"""
        return {
            'prospectus': obj.doc_prospectus,
            'terms': obj.doc_terms,
            'risks': obj.doc_risks,
            'subscription': obj.doc_subscription,
        }


class IssuerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing issuers"""
    
    class Meta:
        model = Issuer
        fields = [
            'id',
            'slug',
            'company_name',
            'security_name',
            'isin',
            'status',
            'offering_page_url',
            'created_at',
        ]
        read_only_fields = fields


class IssuerDocumentSerializer(serializers.ModelSerializer):
    """Serializer for generated issuer documents"""
    
    issuer_name = serializers.CharField(source='issuer.company_name', read_only=True)
    
    class Meta:
        model = IssuerDocument
        fields = [
            'id',
            'issuer',
            'issuer_name',
            'document_type',
            'template_version',
            'file_url',
            'file_hash',
            'generated_at',
            'generated_by',
            'is_current',
        ]
        read_only_fields = ['id', 'generated_at', 'file_hash']
