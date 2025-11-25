from celery import shared_task


@shared_task(bind=True, max_retries=3)
def sync_settlement(self, settlement_id: str):
    """Placeholder: poll upstream and update settlement status."""
    return {"settlementId": settlement_id, "synced": True}
