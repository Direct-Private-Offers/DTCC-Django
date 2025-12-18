from django.db import models
import uuid


class ClearstreamAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    csd_participant = models.CharField(max_length=64)
    csd_account = models.CharField(max_length=64, unique=True)
    lei = models.CharField(max_length=32, null=True, blank=True)
    permissions = models.JSONField(default=list)
    linked = models.BooleanField(default=False)

    def __str__(self):
        return f"CSAccount({self.csd_account})"


class Position(models.Model):
    account = models.CharField(max_length=64, db_index=True)
    isin = models.CharField(max_length=12, db_index=True)
    settled_qty = models.DecimalField(max_digits=36, decimal_places=18)
    pending_qty = models.DecimalField(max_digits=36, decimal_places=18)
    as_of = models.DateTimeField(db_index=True)

    def __str__(self):
        return f"Position({self.account}, {self.isin})"
