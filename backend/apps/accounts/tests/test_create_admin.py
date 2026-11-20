import os
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import User

ADMIN_VARS = ("DJANGO_ADMIN_USERNAME", "DJANGO_ADMIN_EMAIL", "DJANGO_ADMIN_PASSWORD")


def run_create_admin(**env):
    clean = {key: value for key, value in os.environ.items() if key not in ADMIN_VARS}
    clean.update(env)
    out = StringIO()
    with patch.dict(os.environ, clean, clear=True):
        call_command("create_admin", stdout=out)
    return out.getvalue()


class CreateAdminCommandTests(TestCase):
    def test_skips_without_failing_when_password_not_set(self):
        output = run_create_admin()
        self.assertIn("DJANGO_ADMIN_PASSWORD is not set", output)
        self.assertEqual(User.objects.count(), 0)

    def test_creates_admin_with_defaults_for_username_and_email(self):
        run_create_admin(DJANGO_ADMIN_PASSWORD="Str0ngPassw0rd!x")
        user = User.objects.get(username="admin")
        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("Str0ngPassw0rd!x"))

    def test_uses_custom_username_and_email(self):
        run_create_admin(
            DJANGO_ADMIN_USERNAME="owner",
            DJANGO_ADMIN_EMAIL="owner@example.com",
            DJANGO_ADMIN_PASSWORD="Str0ngPassw0rd!x",
        )
        user = User.objects.get(username="owner")
        self.assertEqual(user.email, "owner@example.com")

    def test_is_idempotent(self):
        run_create_admin(DJANGO_ADMIN_PASSWORD="Str0ngPassw0rd!x")
        output = run_create_admin(DJANGO_ADMIN_PASSWORD="Different!Pass1")
        self.assertIn("already exists", output)
        self.assertEqual(User.objects.filter(username="admin").count(), 1)
        self.assertTrue(User.objects.get(username="admin").check_password("Str0ngPassw0rd!x"))
