from .base import *  # noqa: F403
from .base import SECRET_KEY as _BASE_SECRET_KEY

DEBUG = False
SECRET_KEY = _BASE_SECRET_KEY or "test-only-insecure-key"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
