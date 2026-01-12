from django.db import models
from django.contrib.auth.models import User
import uuid


class Receipt(models.Model):
    """Receipt for token distribution events"""
    RECEIPT_TYPES = [
        ('ISSUANCE', 'Issuance Receipt'),
        ('TRANSFER', 'Transfer Receipt'),
        ('SETTLEMENT', 'Settlement Receipt'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt_id = models.CharField(max_length=64, unique=True, db_index=True)
    receipt_type = models.CharField(max_length=20, choices=RECEIPT_TYPES)
    investor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='receipts')
    transaction_id = models.UUIDField(db_index=True)
    isin = models.CharField(max_length=12, null=True, blank=True, db_index=True)
    quantity = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    amount = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    pdf_file = models.FileField(upload_to='receipts/', null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'receipts'
        indexes = [
            models.Index(fields=['investor', 'created_at']),
            models.Index(fields=['receipt_type', 'created_at']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"Receipt({self.receipt_id}, {self.receipt_type})"
