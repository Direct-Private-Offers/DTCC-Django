from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Validate CTA redirect configuration."

    def handle(self, *args, **options):
        base_url = getattr(settings, 'PAYBITO_BASE_URL', '').rstrip('/')
        routes = getattr(settings, 'CTA_REDIRECT_ROUTES', {})

        if not base_url:
            self.stderr.write(self.style.ERROR("PAYBITO_BASE_URL is not configured."))
            return

        if not routes:
            self.stderr.write(self.style.ERROR("CTA_REDIRECT_ROUTES is empty."))
            return

        self.stdout.write(self.style.SUCCESS(f"Base URL: {base_url}"))
        for route, path in routes.items():
            if not path.startswith('/'):
                path = f'/{path}'
            self.stdout.write(f"/r/{route} -> {base_url}{path}")
