"""Infrastructure views with no domain knowledge."""

from django.db import connection
from django.http import HttpRequest, JsonResponse


def healthz(request: HttpRequest) -> JsonResponse:
    """Liveness probe with a real database round-trip (ENH-13a).

    Returns 200 only when a trivial query succeeds, so the check fails loudly
    if the database is unreachable rather than reporting a false positive.
    """
    database_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:  # noqa: BLE001 - any DB error means not-live
        database_ok = False

    payload = {
        "status": "ok" if database_ok else "error",
        "database": "ok" if database_ok else "error",
    }
    return JsonResponse(payload, status=200 if database_ok else 503)
