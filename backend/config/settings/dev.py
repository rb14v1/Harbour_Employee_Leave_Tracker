from .base import *  # noqa: F403
from .base import SECRET_KEY as _BASE_SECRET_KEY

DEBUG = True
SECRET_KEY = _BASE_SECRET_KEY or "dev-only-insecure-key-change-me"
