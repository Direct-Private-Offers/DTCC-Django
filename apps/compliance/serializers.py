"""
Serializers for compliance endpoints.
"""
from rest_framework import serializers
from .models import InvestorProfile, KYCDocument, AMLCheck


class InvestorProfileSerializer(serializers.ModelSerializer):
    """Serializer for investor profile."""
    class Meta:
        model = InvestorProfile
        fields = [
            'id', 'wallet_address', 'investor_type', 'kyc_status',
            'aml_status', 'accredited_investor', 'country_code',
            'kyc_verified_at', 'kyc_expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'kyc_status', 'aml_status', 'kyc_verified_at', 'created_at']


class KYCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for KYC documents."""
    class Meta:
        model = KYCDocument
        fields = [
            'id', 'document_type', 'file_path', 'ipfs_cid',
            'verified', 'verified_at', 'created_at'
        ]
        read_only_fields = ['id', 'verified', 'verified_at', 'created_at']


class AMLCheckSerializer(serializers.ModelSerializer):
    """Serializer for AML checks."""
    class Meta:
        model = AMLCheck
        fields = [
            'id', 'check_type', 'status', 'provider',
            'risk_score', 'checked_at', 'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'checked_at', 'created_at']

