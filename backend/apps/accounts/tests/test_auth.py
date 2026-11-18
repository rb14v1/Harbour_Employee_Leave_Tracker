from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User


class AuthTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = "StrongPass!12345"
        cls.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password=cls.password
        )

    def login(self, username="admin", password=None):
        return self.client.post(
            reverse("auth-login"),
            {"username": username, "password": password or self.password},
            format="json",
        )

    def test_login_returns_access_and_refresh_tokens(self):
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_wrong_password_returns_401(self):
        response = self.login(password="wrong-password")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_missing_fields_returns_400(self):
        response = self.client.post(reverse("auth-login"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self):
        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user(self):
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "admin")
        self.assertNotIn("password", response.data)

    def test_refresh_issues_new_access_token(self):
        tokens = self.login().data
        response = self.client.post(
            reverse("auth-refresh"), {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_with_invalid_token_returns_401(self):
        response = self.client.post(
            reverse("auth-refresh"), {"refresh": "not-a-token"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh_token(self):
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        response = self.client.post(
            reverse("auth-logout"), {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.client.credentials()
        refresh_response = self.client.post(
            reverse("auth-refresh"), {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self):
        tokens = self.login().data
        response = self.client.post(
            reverse("auth-logout"), {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_refresh_token_returns_400(self):
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = self.client.post(
            reverse("auth-logout"), {"refresh": "garbage"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_with_another_users_refresh_token_returns_403(self):
        User.objects.create_user(username="other", email="other@example.com", password=self.password)
        other_refresh = RefreshToken.for_user(User.objects.get(username="other"))
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = self.client.post(
            reverse("auth-logout"), {"refresh": str(other_refresh)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_health_is_public(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
