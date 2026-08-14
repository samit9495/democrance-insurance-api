"""Phase 9: the permission matrix, proven in BOTH DEMO_OPEN_API modes (D4, 9.2).

Deny by default: anonymous is refused when locked and admitted only in demo mode.
A customer principal may act only for itself and sees 404 (never 403) for records
it does not own — no existence leakage. Staff/agent see everything.
"""

import datetime

import pytest
from rest_framework.test import APIClient

from apps.policies import services
from apps.products.models import ProductType

pytestmark = pytest.mark.django_db

PA = "personal-accident"
CUSTOMER_PAYLOAD = {"first_name": "New", "last_name": "Person", "dob": "25-06-1991"}


@pytest.fixture
def world(customer_factory, user_factory):
    """An owning customer (with a policy) and a separate foreign customer."""
    product = ProductType.objects.get(code=PA)

    owner_user = user_factory(email="owner@example.com", role="customer")
    owner = customer_factory(dob=datetime.date(1991, 6, 25))
    owner.user = owner_user
    owner.save(update_fields=["user"])
    own_policy = services.create_quote(
        customer=owner, product=product, as_of=datetime.date(2026, 8, 13)
    )

    foreign = customer_factory(dob=datetime.date(1990, 1, 1))
    foreign_policy = services.create_quote(
        customer=foreign, product=product, as_of=datetime.date(2026, 8, 13)
    )

    staff = user_factory(email="staff@example.com", role="staff", is_staff=True)
    agent = user_factory(email="agent@example.com", role="agent")

    return {
        "owner_user": owner_user,
        "owner": owner,
        "own_policy": own_policy,
        "foreign": foreign,
        "foreign_policy": foreign_policy,
        "staff": staff,
        "agent": agent,
    }


def _client(user=None) -> APIClient:
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


# --- anonymous, both modes ------------------------------------------------

READ_PATHS = ["/api/v1/policies/", "/api/v1/customers/", "/api/v1/search/?q=a"]


@pytest.mark.parametrize("path", READ_PATHS)
def test_anonymous_is_denied_when_locked(settings, path):
    settings.DEMO_OPEN_API = False

    assert _client().get(path).status_code == 401


@pytest.mark.parametrize("path", READ_PATHS)
def test_anonymous_is_admitted_in_demo_mode(settings, path):
    settings.DEMO_OPEN_API = True

    assert _client().get(path).status_code == 200


def test_anonymous_create_customer_locked_is_401(settings):
    settings.DEMO_OPEN_API = False

    response = _client().post("/api/v1/create_customer/", CUSTOMER_PAYLOAD, format="json")
    assert response.status_code == 401


def test_anonymous_create_customer_demo_is_201(settings):
    settings.DEMO_OPEN_API = True

    response = _client().post("/api/v1/create_customer/", CUSTOMER_PAYLOAD, format="json")
    assert response.status_code == 201


# --- customer principal ---------------------------------------------------


def test_customer_cannot_create_customers(settings, world):
    settings.DEMO_OPEN_API = False

    response = _client(world["owner_user"]).post(
        "/api/v1/create_customer/", CUSTOMER_PAYLOAD, format="json"
    )
    assert response.status_code == 403


def test_customer_sees_its_own_policy(settings, world):
    settings.DEMO_OPEN_API = False

    response = _client(world["owner_user"]).get(f"/api/v1/policies/{world['own_policy'].id}/")
    assert response.status_code == 200


def test_customer_gets_404_not_403_for_a_foreign_policy(settings, world):
    settings.DEMO_OPEN_API = False

    response = _client(world["owner_user"]).get(f"/api/v1/policies/{world['foreign_policy'].id}/")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_customer_list_is_scoped_to_its_own_policies(settings, world):
    settings.DEMO_OPEN_API = False

    body = _client(world["owner_user"]).get("/api/v1/policies/").json()
    assert [row["id"] for row in body["results"]] == [world["own_policy"].id]


def test_customer_cannot_quote_for_another_customer(settings, world):
    settings.DEMO_OPEN_API = False

    response = _client(world["owner_user"]).post(
        "/api/v1/quote/", {"customer_id": world["foreign"].id, "type": PA}, format="json"
    )
    assert response.status_code == 404


# --- privileged principals ------------------------------------------------


@pytest.mark.parametrize("who", ["staff", "agent"])
def test_privileged_principals_see_foreign_policies(settings, world, who):
    settings.DEMO_OPEN_API = False

    response = _client(world[who]).get(f"/api/v1/policies/{world['foreign_policy'].id}/")
    assert response.status_code == 200
