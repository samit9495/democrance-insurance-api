"""Test settings: fast in-memory SQLite, deterministic and Docker-free.

CI additionally runs the whole suite against PostgreSQL by exporting
DATABASE_URL, so no Postgres-specific behaviour goes unverified.
"""

from .base import *  # noqa: F403

DEBUG = False

# WhiteNoise scans STATIC_ROOT at startup and warns when it is absent; it adds
# nothing under test, so drop it to keep the suite output clean.
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m.lower()]  # noqa: F405

# The manifest static storage needs a collectstatic run; use the plain storage
# so admin templates ({% static %}) render under test without one.
STORAGES = {  # noqa: F405
    **STORAGES,  # noqa: F405
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Honour DATABASE_URL when CI sets it (PostgreSQL leg); otherwise in-memory SQLite.
if not DATABASE_URL:  # noqa: F405
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
