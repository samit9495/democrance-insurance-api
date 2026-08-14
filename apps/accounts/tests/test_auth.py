"""Phase 9: JWT lifecycle and the demo-mode startup warning (REQUIREMENTS 8.3, 9.2)."""

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.apps import warn_if_demo_open

pytestmark = pytest.mark.django_db

CREDS = {"email": "s@example.com", "password": "password123"}


@pytest.fixture
def staff(user_factory):
    return user_factory(email=CREDS["email"], role="staff", is_staff=True)


def _obtain(client) -> dict:
    return client.post("/api/v1/auth/token/", CREDS, format="json").json()


def test_token_obtain_returns_access_and_refresh(anon_client, staff):
    response = anon_client.post("/api/v1/auth/token/", CREDS, format="json")

    assert response.status_code == 200
    assert {"access", "refresh"} <= set(response.json())


def test_bad_credentials_are_a_uniform_401(anon_client, staff):
    response = anon_client.post("/api/v1/auth/token/", {**CREDS, "password": "nope"}, format="json")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"


def test_refresh_rotates_and_blacklists_the_old_token(anon_client, staff):
    tokens = _obtain(anon_client)

    rotated = anon_client.post(
        "/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]}, format="json"
    )
    assert rotated.status_code == 200
    assert {"access", "refresh"} <= set(rotated.json())

    # Rotation blacklists the presented refresh, so reusing it must fail.
    reused = anon_client.post(
        "/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]}, format="json"
    )
    assert reused.status_code == 401


def test_logout_blacklists_the_refresh_token(anon_client, staff):
    tokens = _obtain(anon_client)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    out = client.post("/api/v1/auth/logout/", {"refresh": tokens["refresh"]}, format="json")
    assert out.status_code == 200

    reused = anon_client.post(
        "/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]}, format="json"
    )
    assert reused.status_code == 401


def test_me_returns_role_and_linked_customer_id(customer_factory, user_factory):
    import datetime

    user = user_factory(email="c@example.com", role="customer")
    customer = customer_factory(dob=datetime.date(1991, 6, 25))
    customer.user = user
    customer.save(update_fields=["user"])
    client = APIClient()
    client.force_authenticate(user=user)

    body = client.get("/api/v1/auth/me/").json()

    assert body["role"] == "customer"
    assert body["customer_id"] == customer.id


def test_me_requires_authentication(anon_client):
    # /me/ is IsAuthenticated even in demo mode: it is about the caller's identity.
    assert anon_client.get("/api/v1/auth/me/").status_code == 401


def test_token_endpoint_is_throttled(anon_client, staff):
    statuses = [
        anon_client.post("/api/v1/auth/token/", CREDS, format="json").status_code for _ in range(6)
    ]

    assert 429 in statuses


def test_demo_mode_logs_a_startup_warning(caplog):
    with override_settings(DEMO_OPEN_API=True), caplog.at_level("WARNING"):
        assert warn_if_demo_open() is True
    assert any("DEMO_OPEN_API" in record.message for record in caplog.records)


def test_no_warning_when_locked_down():
    with override_settings(DEMO_OPEN_API=False):
        assert warn_if_demo_open() is False
