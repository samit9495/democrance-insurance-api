"""Guard against models drifting away from their migrations.

``makemigrations --check`` exits non-zero when a model change has not been
captured in a migration; running it as a test means a forgotten migration fails
CI instead of surprising the next person to deploy.
"""

from io import StringIO

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_no_missing_migrations():
    try:
        call_command(
            "makemigrations",
            "--check",
            "--dry-run",
            stdout=StringIO(),
            stderr=StringIO(),
        )
    except SystemExit as exc:  # pragma: no cover - only hit when drift exists
        pytest.fail(
            f"Model changes are not reflected in migrations "
            f"(makemigrations --check exited {exc.code}). Run `make makemigrations`."
        )
