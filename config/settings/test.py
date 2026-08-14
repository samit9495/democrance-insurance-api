"""Test settings: fast in-memory SQLite, deterministic and Docker-free.

CI additionally runs the whole suite against PostgreSQL by exporting
DATABASE_URL, so no Postgres-specific behaviour goes unverified.
"""

from .base import *  # noqa: F403

DEBUG = False

# Honour DATABASE_URL when CI sets it (PostgreSQL leg); otherwise in-memory SQLite.
if not DATABASE_URL:  # noqa: F405
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
