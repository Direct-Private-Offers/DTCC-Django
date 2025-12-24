"""
Django signals for automatic notifications.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.dex.models import Order, Trade
from apps.settlement.models import Settlement
from apps.compliance.models import InvestorProfile
from .services import (
    notify_order_filled, notify_settlement_complete, notify_kyc_approved
)


@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    """Notify when order status changes to FILLED."""
    if instance.status == Order.OrderStatus.FILLED and not created:
        notify_order_filled(
            user=instance.wallet.user,
            order_id=str(instance.id),
            isin=instance.isin,
            quantity=str(instance.quantity)
        )


@receiver(post_save, sender=Settlement)
def notify_settlement_status_change(sender, instance, created, **kwargs):
    """Notify when settlement status changes to SETTLED."""
    if instance.status == Settlement.Status.SETTLED and not created:
        # Note: Settlement doesn't have direct user reference
        # Would need to look up user from account or other field
        pass


@receiver(post_save, sender=InvestorProfile)
def notify_kyc_status_change(sender, instance, created, **kwargs):
    """Notify when KYC status changes to APPROVED."""
    if instance.kyc_status == InvestorProfile.KYCStatus.APPROVED and not created:
        notify_kyc_approved(user=instance.user)

