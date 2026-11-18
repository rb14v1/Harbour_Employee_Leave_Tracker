from .base import *  # noqa: F403
from .base import SECRET_KEY as _BASE_SECRET_KEY

DEBUG = False
SECRET_KEY = _BASE_SECRET_KEY or "test-only-insecure-key-0123456789abcdef0123"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
