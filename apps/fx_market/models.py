from django.db import models
from django.contrib.auth.models import User
import uuid


class FxConversion(models.Model):
    """FX conversion record"""
    CONVERSION_TYPE_CHOICES = [
        ('FX_TO_TOKEN', 'FX to Token'),
        ('TOKEN_TO_FX', 'Token to FX'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fx_conversions')
    conversion_type = models.CharField(max_length=20, choices=CONVERSION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Source amount and currency
    source_amount = models.DecimalField(max_digits=36, decimal_places=18)
    source_currency = models.CharField(max_length=3)
    
    # Target amount and currency/token
    target_amount = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    target_currency = models.CharField(max_length=3, null=True, blank=True)
    token_address = models.CharField(max_length=42, null=True, blank=True)
    
    # Conversion details
    conversion_rate = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    fee = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    fx_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    blockchain_tx_hash = models.CharField(max_length=66, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'fx_conversions'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['conversion_type', 'status']),
            models.Index(fields=['fx_transaction_id']),
        ]
    
    def __str__(self):
        return f"FxConversion({self.conversion_type}, {self.status})"


class CrossPlatformSettlement(models.Model):
    """Cross-platform settlement record"""
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('ROLLED_BACK', 'Rolled Back'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dpo_settlement_id = models.UUIDField(unique=True, db_index=True)
    fx_settlement_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    
    # Settlement details
    isin = models.CharField(max_length=12, null=True, blank=True)
    quantity = models.DecimalField(max_digits=36, decimal_places=18)
    amount = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    # Reconciliation
    dpo_status = models.CharField(max_length=50, null=True, blank=True)
    fx_status = models.CharField(max_length=50, null=True, blank=True)
    reconciled = models.BooleanField(default=False)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(null=True, blank=True)
    rollback_reason = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'cross_platform_settlements'
        indexes = [
            models.Index(fields=['dpo_settlement_id']),
            models.Index(fields=['fx_settlement_id']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['reconciled']),
        ]
    
    def __str__(self):
        return f"CrossPlatformSettlement({self.dpo_settlement_id}, {self.status})"


class TokenFlow(models.Model):
    """Token flow record between DPO and FX-to-market"""
    FLOW_DIRECTION_CHOICES = [
        ('DPO_TO_FX', 'DPO to FX-to-Market'),
        ('FX_TO_DPO', 'FX-to-Market to DPO'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token_flows')
    flow_direction = models.CharField(max_length=20, choices=FLOW_DIRECTION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Token details
    token_address = models.CharField(max_length=42)
    amount = models.DecimalField(max_digits=36, decimal_places=18)
    
    # Transaction tracking
    blockchain_tx_hash = models.CharField(max_length=66, null=True, blank=True)
    fx_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Balance sync
    dpo_balance_before = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    dpo_balance_after = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    fx_balance_before = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    fx_balance_after = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'token_flows'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['flow_direction', 'status']),
            models.Index(fields=['blockchain_tx_hash']),
            models.Index(fields=['fx_transaction_id']),
        ]
    
    def __str__(self):
        return f"TokenFlow({self.flow_direction}, {self.status})"

