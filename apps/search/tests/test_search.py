"""Phase 8: unified /api/v1/search/ across customers and policies (REQUIREMENTS 8.2).

One call returns both entities with counts, narrows by ``entity``, rejects an
unknown ``entity``, and safely parameterises a hostile ``q``.
"""

import datetime

import pytest

from apps.policies import services
from apps.products.models import ProductType

pytestmark = pytest.mark.django_db

TODAY = datetime.date(2026, 8, 13)


@pytest.fixture
def stokes_with_quote(customer_factory):
    customer = customer_factory(
        first_name="Ben", last_name="Stokes", dob=datetime.date(1991, 6, 25)
    )
    pa = ProductType.objects.get(code="personal-accident")
    services.create_quote(customer=customer, product=pa, as_of=TODAY)
    return customer


def test_search_returns_both_entities_with_counts(staff_client, stokes_with_quote):
    body = staff_client.get("/api/v1/search/?q=stokes").json()

    assert set(body) == {"customers", "policies"}
    assert body["customers"]["count"] == 1
    assert body["policies"]["count"] == 1
    assert body["customers"]["results"][0]["last_name"] == "Stokes"


def test_entity_narrows_the_result(staff_client, stokes_with_quote):
    body = staff_client.get("/api/v1/search/?q=stokes&entity=customers").json()

    assert set(body) == {"customers"}
    assert body["customers"]["count"] == 1


def test_unknown_entity_is_400(staff_client):
    response = staff_client.get("/api/v1/search/?entity=aliens")

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "entity" in error["details"]


def test_hostile_q_is_safely_parameterised(staff_client, stokes_with_quote):
    from apps.customers.models import Customer

    response = staff_client.get("/api/v1/search/?q=%27%3B+DROP+TABLE+customers_customer%3B+--")

    assert response.status_code == 200
    body = response.json()
    assert body["customers"]["count"] == 0
    # The table is intact: the ORM parameterised the value, it did not execute it.
    assert Customer.objects.count() == 1
