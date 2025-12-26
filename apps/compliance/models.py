"""
KYC/AML compliance models for investor verification.
"""
from django.db import models
from django.contrib.auth.models import User
import uuid


class InvestorProfile(models.Model):
    """Investor profile with KYC/AML information."""
    class KYCStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'
    
    class InvestorType(models.TextChoices):
        INDIVIDUAL = 'INDIVIDUAL', 'Individual'
        INSTITUTIONAL = 'INSTITUTIONAL', 'Institutional'
        ACCREDITED = 'ACCREDITED', 'Accredited Investor'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='investor_profile')
    wallet_address = models.CharField(max_length=128, unique=True, db_index=True)
    investor_type = models.CharField(max_length=16, choices=InvestorType.choices)
    kyc_status = models.CharField(max_length=16, choices=KYCStatus.choices, default=KYCStatus.PENDING)
    aml_status = models.CharField(max_length=16, default='PENDING')
    accredited_investor = models.BooleanField(default=False)
    country_code = models.CharField(max_length=2, null=True, blank=True)
    tax_id = models.CharField(max_length=64, null=True, blank=True)
    kyc_verified_at = models.DateTimeField(null=True, blank=True)
    kyc_expires_at = models.DateTimeField(null=True, blank=True)
    # NEO Bank integration fields
    neo_bank_synced = models.BooleanField(default=False)
    neo_bank_sync_status = models.CharField(max_length=20, null=True, blank=True)  # PENDING, SYNCED, CONFLICT, ERROR
    neo_bank_last_synced = models.DateTimeField(null=True, blank=True)
    neo_bank_account_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_investor_profiles'
        indexes = [
            models.Index(fields=['wallet_address']),
            models.Index(fields=['kyc_status', 'aml_status']),
            models.Index(fields=['investor_type']),
            models.Index(fields=['neo_bank_synced', 'neo_bank_sync_status']),
            models.Index(fields=['neo_bank_account_id']),
        ]
    
    def __str__(self):
        return f"InvestorProfile({self.user.username}, {self.kyc_status})"


class KYCDocument(models.Model):
    """KYC verification documents."""
    class DocumentType(models.TextChoices):
        PASSPORT = 'PASSPORT', 'Passport'
        DRIVERS_LICENSE = 'DRIVERS_LICENSE', "Driver's License"
        NATIONAL_ID = 'NATIONAL_ID', 'National ID'
        PROOF_OF_ADDRESS = 'PROOF_OF_ADDRESS', 'Proof of Address'
        BANK_STATEMENT = 'BANK_STATEMENT', 'Bank Statement'
        TAX_DOCUMENT = 'TAX_DOCUMENT', 'Tax Document'
        OTHER = 'OTHER', 'Other'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(InvestorProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=32, choices=DocumentType.choices)
    file_path = models.CharField(max_length=512)
    ipfs_cid = models.CharField(max_length=128, null=True, blank=True)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'compliance_kyc_documents'
        indexes = [
            models.Index(fields=['investor', 'document_type']),
            models.Index(fields=['verified']),
        ]
    
    def __str__(self):
        return f"KYCDocument({self.document_type}, {self.investor.user.username})"


class AMLCheck(models.Model):
    """AML screening check records."""
    class CheckStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CLEAR = 'CLEAR', 'Clear'
        FLAGGED = 'FLAGGED', 'Flagged'
        BLOCKED = 'BLOCKED', 'Blocked'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(InvestorProfile, on_delete=models.CASCADE, related_name='aml_checks')
    check_type = models.CharField(max_length=64)  # SANCTIONS, PEP, ADVERSE_MEDIA, etc.
    status = models.CharField(max_length=16, choices=CheckStatus.choices, default=CheckStatus.PENDING)
    provider = models.CharField(max_length=64, null=True, blank=True)  # Screening provider
    reference_id = models.CharField(max_length=128, null=True, blank=True)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    details = models.JSONField(default=dict)
    checked_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'compliance_aml_checks'
        indexes = [
            models.Index(fields=['investor', 'status']),
            models.Index(fields=['check_type', 'status']),
            models.Index(fields=['checked_at']),
        ]
    
    def __str__(self):
        return f"AMLCheck({self.check_type}, {self.status})"


class AuditLog(models.Model):
    """Comprehensive audit log for compliance and security."""
    class ActionType(models.TextChoices):
        CREATE = 'CREATE', 'Create'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'
        VIEW = 'VIEW', 'View'
        APPROVE = 'APPROVE', 'Approve'
        REJECT = 'REJECT', 'Reject'
        TRANSFER = 'TRANSFER', 'Transfer'
        TRADE = 'TRADE', 'Trade'
        SWAP = 'SWAP', 'Swap'
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action_type = models.CharField(max_length=16, choices=ActionType.choices)
    resource_type = models.CharField(max_length=64)  # Order, Swap, Settlement, etc.
    resource_id = models.CharField(max_length=128, null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    request_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    changes = models.JSONField(null=True, blank=True)  # Before/after values
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'compliance_audit_logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['request_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"AuditLog({self.action_type}, {self.resource_type}, {self.created_at})"

