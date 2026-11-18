from django.conf import settings
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def revoke_refresh_token(user, raw_token):
    try:
        token = RefreshToken(raw_token)
    except TokenError as exc:
        raise ValidationError({"refresh": "Invalid or expired refresh token."}) from exc

    claim = settings.SIMPLE_JWT["USER_ID_CLAIM"]
    if str(token.get(claim)) != str(user.pk):
        raise PermissionDenied("Refresh token does not belong to the authenticated user.")

    token.blacklist()
