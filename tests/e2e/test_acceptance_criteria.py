"""Acceptance-criteria tests, phrased in the brief's own words.

These assert the two headline outcomes the brief calls out explicitly: a
customer can be created from the documented payload and is then visible to the
business, and a personal-accident quote for the sample customer prices at 200.
"""

import datetime

import pytest
import time_machine

TODAY = datetime.date(2026, 8, 13)
PA = "personal-accident"


@pytest.mark.django_db
def test_a_customer_can_be_created_and_is_then_visible(anon_client):
    """AC: 'create a customer' -> the record exists and is findable by search."""
    created = anon_client.post(
        "/api/v1/create_customer/",
        {"first_name": "Ben", "last_name": "Stokes", "dob": "25-06-1991"},
        format="json",
    )
    assert created.status_code == 201
    body = created.json()
    assert body["first_name"] == "Ben"
    assert body["dob"] == "25-06-1991"

    found = anon_client.get("/api/v1/search/?q=Stokes&entity=customers")
    assert found.status_code == 200
    section = found.json()["customers"]
    assert section["count"] == 1
    assert section["results"][0]["last_name"] == "Stokes"


@time_machine.travel(TODAY)
@pytest.mark.django_db
def test_a_personal_accident_quote_prices_at_the_expected_premium(anon_client, customer_factory):
    """AC: quoting the sample customer for personal-accident returns premium 200."""
    customer = customer_factory(
        first_name="Ben", last_name="Stokes", dob=datetime.date(1991, 6, 25)
    )

    quoted = anon_client.post(
        "/api/v1/quote/", {"customer_id": customer.id, "type": PA}, format="json"
    )
    assert quoted.status_code == 201
    assert quoted.json()["premium"] == "200.00"
