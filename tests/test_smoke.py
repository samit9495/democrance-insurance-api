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


@pytest.mark.django_db
def test_healthz_reports_error_when_database_is_unreachable(client, monkeypatch):
    """The probe fails loudly with 503 when the DB round-trip errors (ENH-13a)."""
    from apps.common import views

    def boom(*args, **kwargs):
        raise RuntimeError("database unreachable")

    monkeypatch.setattr(views.connection, "cursor", boom)

    response = client.get("/healthz/")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["database"] == "error"


def test_settings_fall_back_to_sqlite_without_database_url(settings):
    """DATABASE_URL selects PostgreSQL; its absence falls back to SQLite (D5).

    CI runs this on both legs of the matrix, so assert the contract in the
    direction that matches the current environment rather than hard-coding one.
    """
    engine = settings.DATABASES["default"]["ENGINE"]
    if settings.DATABASE_URL:
        assert engine.endswith("postgresql")
    else:
        assert engine.endswith("sqlite3")
