"""Development settings: DEBUG on, permissive hosts, zero-setup SQLite default."""

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
