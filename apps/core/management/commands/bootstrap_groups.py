from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


DEFAULT_GROUPS = [
    "issuer",      # Can initiate issuance instructions and corporate actions
    "reporter",    # Can report derivatives
    "ops",         # Operational actions (e.g., Clearstream writes)
]


class Command(BaseCommand):
    help = "Create default RBAC groups required by the API (issuer, reporter)."

    def handle(self, *args, **options):
        created = []
        for name in DEFAULT_GROUPS:
            group, was_created = Group.objects.get_or_create(name=name)
            if was_created:
                created.append(name)

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created groups: {', '.join(created)}"))
        else:
            self.stdout.write("Groups already exist; no changes.")
