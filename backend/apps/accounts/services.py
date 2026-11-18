from django.conf import settings
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


def get_demo_tokens():
    user, created = User.objects.get_or_create(
        username=settings.DEMO_ADMIN_USERNAME,
        defaults={"email": "demo@example.invalid", "is_staff": True, "is_superuser": True},
    )
    if created or user.has_usable_password():
        user.set_unusable_password()
        user.save(update_fields=["password"])
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def revoke_refresh_token(user, raw_token):
    try:
        token = RefreshToken(raw_token)
    except TokenError as exc:
        raise ValidationError({"refresh": "Invalid or expired refresh token."}) from exc

    claim = settings.SIMPLE_JWT["USER_ID_CLAIM"]
    if str(token.get(claim)) != str(user.pk):
        raise PermissionDenied("Refresh token does not belong to the authenticated user.")

    token.blacklist()
