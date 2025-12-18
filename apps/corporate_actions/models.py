from django.db import models
import uuid


class CorporateAction(models.Model):
    class Types(models.TextChoices):
        DIVIDEND = 'DIVIDEND', 'DIVIDEND'
        SPLIT = 'SPLIT', 'SPLIT'
        MERGER = 'MERGER', 'MERGER'
        RIGHTS_ISSUE = 'RIGHTS_ISSUE', 'RIGHTS_ISSUE'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    isin = models.CharField(max_length=12, db_index=True)
    type = models.CharField(max_length=16, choices=Types.choices)
    record_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    factor = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    amount_per_share = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    currency = models.CharField(max_length=8, null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=128, null=True, blank=True)
    action_data = models.JSONField(default=dict, null=True, blank=True)
    status = models.CharField(max_length=16, default='SCHEDULED')
    tx_hash = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CorporateAction({self.id}, {self.isin}, {self.type}, {self.status})"
