from django.apps import AppConfig
import os


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    
    def ready(self):
        # Allow disabling notifications init for local/dev where third-party email libs
        # may not be installed (e.g., sendgrid). Controlled via env var.
        if os.environ.get('DISABLE_NOTIFICATIONS', '').lower() in ('1', 'true', 'yes'):
            return
        import apps.notifications.signals  # noqa

