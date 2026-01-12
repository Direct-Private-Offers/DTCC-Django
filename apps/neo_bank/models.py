from django.db import models
from django.contrib.auth.models import User
import uuid


class NeoBankAccountLink(models.Model):
    """Link between DPO user and NEO bank account"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='neo_bank_account')
    neo_account_id = models.CharField(max_length=255, unique=True, db_index=True)
    permissions = models.JSONField(default=list, blank=True)
    linked_at = models.DateTimeField(auto_now_add=True)
    last_synced = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'neo_bank_account_links'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['neo_account_id']),
        ]
    
    def __str__(self):
        return f"NeoBankLink({self.user.username} -> {self.neo_account_id})"


class KycSyncStatus(models.Model):
    """KYC synchronization status between DPO and NEO bank"""
    SYNC_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SYNCED', 'Synced'),
        ('CONFLICT', 'Conflict'),
        ('ERROR', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_sync_statuses')
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='PENDING')
    dpo_kyc_data = models.JSONField(default=dict, blank=True)
    neo_kyc_data = models.JSONField(default=dict, blank=True)
    conflict_details = models.JSONField(default=dict, blank=True)
    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'kyc_sync_statuses'
        indexes = [
            models.Index(fields=['user', 'sync_status']),
            models.Index(fields=['sync_status', 'last_synced']),
        ]
    
    def __str__(self):
        return f"KycSync({self.user.username}, {self.sync_status})"


class TransactionSync(models.Model):
    """Transaction synchronization record"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.UUIDField(unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaction_syncs')
    synced_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=20, default='PENDING')
    neo_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'transaction_syncs'
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user', 'synced_at']),
        ]
    
    def __str__(self):
        return f"TransactionSync({self.transaction_id})"

