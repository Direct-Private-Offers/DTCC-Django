"""
Issuer Signals
Auto-generate offering pages, send notifications, etc.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Issuer


@receiver(post_save, sender=Issuer)
def issuer_post_save(sender, instance, created, **kwargs):
    """
    Post-save signal for Issuer model.
    Triggers offering page generation, notifications, etc.
    """
    if created:
        # New issuer created - could trigger:
        # - Email notification to admin
        # - Offering page generation
        # - Document template population
        # - Omnisend automation trigger
        pass
    else:
        # Issuer updated - could trigger:
        # - Offering page regeneration if published
        # - Notification of changes
        pass
