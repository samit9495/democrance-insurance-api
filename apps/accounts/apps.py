import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger("apps.accounts")


def warn_if_demo_open() -> bool:
    """Log a loud warning when the API is left open (D4). Returns whether it did."""
    if getattr(settings, "DEMO_OPEN_API", False):
        logger.warning(
            "DEMO_OPEN_API is ON: the API is reachable without authentication. "
            "This must be false in any real deployment."
        )
        return True
    return False


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self):
        warn_if_demo_open()
