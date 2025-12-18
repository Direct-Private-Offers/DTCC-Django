from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.core.models import WebhookReplay


class Command(BaseCommand):
    help = 'Clean up old webhook replay nonces (older than 24 hours)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Age in hours for nonces to be considered expired (default: 24)',
        )

    def handle(self, *args, **options):
        hours = options['hours']
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        deleted_count, _ = WebhookReplay.objects.filter(
            created_at__lt=cutoff_time
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {deleted_count} webhook replay nonces older than {hours} hours'
            )
        )

