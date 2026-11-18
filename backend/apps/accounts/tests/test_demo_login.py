from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class DemoLoginTests(APITestCase):
    def test_config_reports_demo_mode_off_by_default(self):
        response = self.client.get(reverse("auth-config"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["demo_mode"])

    def test_demo_login_is_not_found_when_disabled(self):
        response = self.client.post(reverse("auth-demo-login"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(User.objects.filter(username="demo").exists())

    @override_settings(DEMO_AUTO_LOGIN=True, DEMO_ADMIN_USERNAME="demo")
    def test_config_reports_demo_mode_on(self):
        response = self.client.get(reverse("auth-config"))
        self.assertTrue(response.data["demo_mode"])

    @override_settings(DEMO_AUTO_LOGIN=True, DEMO_ADMIN_USERNAME="demo")
    def test_demo_login_returns_tokens_that_authenticate(self):
        response = self.client.post(reverse("auth-demo-login"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        me = self.client.get(reverse("auth-me"))
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["username"], "demo")

    @override_settings(DEMO_AUTO_LOGIN=True, DEMO_ADMIN_USERNAME="demo")
    def test_repeated_demo_login_reuses_one_user(self):
        self.client.post(reverse("auth-demo-login"))
        self.client.post(reverse("auth-demo-login"))
        self.assertEqual(User.objects.filter(username="demo").count(), 1)

    @override_settings(DEMO_AUTO_LOGIN=True, DEMO_ADMIN_USERNAME="demo")
    def test_demo_user_cannot_sign_in_with_password_login(self):
        self.client.post(reverse("auth-demo-login"))
        response = self.client.post(
            reverse("auth-login"), {"username": "demo", "password": "GuessPass!12345"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(User.objects.get(username="demo").has_usable_password())

    @override_settings(DEMO_AUTO_LOGIN=True, DEMO_ADMIN_USERNAME="demo")
    def test_existing_user_with_password_is_locked_down_on_demo_login(self):
        User.objects.create_user(username="demo", email="demo@example.invalid", password="SomePass!12345")
        self.client.post(reverse("auth-demo-login"))
        self.assertFalse(User.objects.get(username="demo").has_usable_password())

    def test_protected_routes_still_require_token_when_demo_mode_on(self):
        with override_settings(DEMO_AUTO_LOGIN=True):
            response = self.client.get(reverse("leave-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
