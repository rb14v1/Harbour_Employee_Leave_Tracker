import os

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User

DEFAULT_USERNAME = "admin"
DEFAULT_EMAIL = "admin@example.com"


class Command(BaseCommand):
    help = (
        "Create the administrator account from DJANGO_ADMIN_USERNAME (default 'admin'), "
        "DJANGO_ADMIN_EMAIL (default 'admin@example.com') and DJANGO_ADMIN_PASSWORD (required, no default). "
        "Skips with a warning when no password is set. Idempotent: does nothing if the user exists."
    )

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_ADMIN_USERNAME", "").strip() or DEFAULT_USERNAME
        email = os.environ.get("DJANGO_ADMIN_EMAIL", "").strip() or DEFAULT_EMAIL
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "")

        if not password:
            self.stdout.write(
                self.style.WARNING(
                    "DJANGO_ADMIN_PASSWORD is not set. Skipping admin creation. "
                    "Set it in backend/.env to create the admin account."
                )
            )
            return

        with transaction.atomic():
            if User.objects.filter(username=username).exists():
                self.stdout.write(f"Admin user '{username}' already exists. Skipping.")
                return

            User.objects.create_superuser(username=username, email=email, password=password)

        self.stdout.write(self.style.SUCCESS(f"Admin user '{username}' created."))
