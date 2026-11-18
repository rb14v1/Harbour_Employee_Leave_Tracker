import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User


class Command(BaseCommand):
    help = (
        "Create the administrator account from DJANGO_ADMIN_USERNAME, "
        "DJANGO_ADMIN_EMAIL and DJANGO_ADMIN_PASSWORD. Idempotent: does nothing if the user exists."
    )

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_ADMIN_USERNAME", "").strip()
        email = os.environ.get("DJANGO_ADMIN_EMAIL", "").strip()
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "")

        if not username or not email or not password:
            raise CommandError(
                "DJANGO_ADMIN_USERNAME, DJANGO_ADMIN_EMAIL and DJANGO_ADMIN_PASSWORD must be set."
            )

        with transaction.atomic():
            if User.objects.filter(username=username).exists():
                self.stdout.write(f"Admin user '{username}' already exists. Skipping.")
                return

            User.objects.create_superuser(username=username, email=email, password=password)

        self.stdout.write(self.style.SUCCESS(f"Admin user '{username}' created."))
