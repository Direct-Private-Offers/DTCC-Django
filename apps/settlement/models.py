from django.db import models
import uuid


class Settlement(models.Model):
    class Source(models.TextChoices):
        EUROCLEAR = 'euroclear', 'Euroclear'
        CLEARSTREAM = 'clearstream', 'Clearstream'

    class Status(models.TextChoices):
        INITIATED = 'INITIATED', 'INITIATED'
        MATCHED = 'MATCHED', 'MATCHED'
        SETTLED = 'SETTLED', 'SETTLED'
        FAILED = 'FAILED', 'FAILED'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.EUROCLEAR)
    isin = models.CharField(max_length=12, db_index=True)
    quantity = models.DecimalField(max_digits=36, decimal_places=18)
    trade_date = models.DateField(null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)
    counterparty = models.CharField(max_length=128, null=True, blank=True)
    account = models.CharField(max_length=128, null=True, blank=True)
    pmi_reference = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.INITIATED, db_index=True)
    timeline = models.JSONField(default=dict)
    tx_hash = models.CharField(max_length=128, null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    # FX-to-Market integration fields
    fx_market_synced = models.BooleanField(default=False)
    fx_market_settlement_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    fx_market_status = models.CharField(max_length=50, null=True, blank=True)
    fx_market_reconciled = models.BooleanField(default=False)
    fx_market_reconciled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['isin', 'status']),
            models.Index(fields=['fx_market_synced', 'fx_market_reconciled']),
            models.Index(fields=['fx_market_settlement_id']),
        ]

    def __str__(self):
        return f"Settlement({self.id}, {self.isin}, {self.status})"
