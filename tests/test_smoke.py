"""Phase 0 walking-skeleton smoke tests (REQ-P1-1, ENH-10, ENH-13a)."""

import pytest


@pytest.mark.django_db
def test_healthz_returns_ok(client):
    """The liveness probe returns 200 with an ok status after a DB round-trip."""
    response = client.get("/healthz/")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_settings_fall_back_to_sqlite_without_database_url(settings):
    """With no DATABASE_URL the default database is SQLite — zero-setup (D5)."""
    assert settings.DATABASES["default"]["ENGINE"].endswith("sqlite3")
