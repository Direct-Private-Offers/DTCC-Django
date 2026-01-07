from django.apps import AppConfig


class IssuersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.issuers'
    verbose_name = 'Issuer Onboarding'
    
    def ready(self):
        """Import signals when app is ready"""
        import apps.issuers.signals
