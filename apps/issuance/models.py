from django.db import models
import uuid


class BlockchainEvent(models.Model):
    """Base model for blockchain events."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block_number = models.BigIntegerField(db_index=True)
    tx_hash = models.CharField(max_length=128, db_index=True)
    event_type = models.CharField(max_length=64, db_index=True)
    event_data = models.JSONField()
    processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['block_number', 'processed']),
            models.Index(fields=['tx_hash']),
            models.Index(fields=['event_type', 'processed']),
        ]

    def __str__(self):
        return f"{self.event_type} at block {self.block_number}"


class IssuanceEvent(BlockchainEvent):
    """Token issuance events from smart contract."""
    isin = models.CharField(max_length=12, db_index=True)
    investor_address = models.CharField(max_length=128, db_index=True)
    amount = models.DecimalField(max_digits=36, decimal_places=18)
    transaction_id = models.CharField(max_length=128, null=True, blank=True)
    euroclear_ref = models.CharField(max_length=128, null=True, blank=True)

    class Meta:
        db_table = 'issuance_events'
        indexes = [
            models.Index(fields=['isin', 'processed']),
            models.Index(fields=['investor_address']),
        ]

    def __str__(self):
        return f"IssuanceEvent({self.isin}, {self.investor_address}, {self.amount})"


class TransferEvent(BlockchainEvent):
    """Token transfer events from smart contract."""
    isin = models.CharField(max_length=12, db_index=True)
    from_address = models.CharField(max_length=128, db_index=True)
    to_address = models.CharField(max_length=128, db_index=True)
    amount = models.DecimalField(max_digits=36, decimal_places=18)

    class Meta:
        db_table = 'transfer_events'
        indexes = [
            models.Index(fields=['isin', 'processed']),
            models.Index(fields=['from_address', 'to_address']),
        ]

    def __str__(self):
        return f"TransferEvent({self.isin}, {self.from_address} -> {self.to_address}, {self.amount})"

