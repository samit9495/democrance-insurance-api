"""Phase 2: create_customer API (REQ-P1-2/4, diagram step 1).

Exercises the brief's exact payload, all route spellings (RPC + REST alias,
with and without the trailing slash), the uniform 400 envelope, and 405.
"""

import datetime

import pytest
import time_machine

from apps.customers.models import Customer

TODAY = datetime.date(2026, 8, 13)
BRIEF_PAYLOAD = {"first_name": "Ben", "last_name": "Stokes", "dob": "25-06-1991"}


@pytest.mark.django_db
@time_machine.travel(TODAY)
def test_create_customer_with_brief_payload_returns_201_and_persists(staff_client):
    response = staff_client.post("/api/v1/create_customer/", BRIEF_PAYLOAD, format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["first_name"] == "Ben"
    assert body["last_name"] == "Stokes"
    assert body["dob"] == "25-06-1991"
    assert body["age"] == 35
    assert Customer.objects.filter(id=body["id"]).exists()


@pytest.mark.django_db
@time_machine.travel(TODAY)
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/create_customer/",
        "/api/v1/create_customer",
        "/api/v1/customers/",
        "/api/v1/customers",
    ],
)
def test_all_route_spellings_create_a_customer(staff_client, path):
    response = staff_client.post(path, BRIEF_PAYLOAD, format="json")

    assert response.status_code == 201


@pytest.mark.django_db
@time_machine.travel(TODAY)
@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"first_name": "Ben", "last_name": "Stokes"}, "dob"),
        ({**BRIEF_PAYLOAD, "dob": "2027-01-01"}, "dob"),
        ({**BRIEF_PAYLOAD, "dob": "not-a-date"}, "dob"),
        ({**BRIEF_PAYLOAD, "premium": "5.00"}, "premium"),
    ],
)
def test_invalid_payloads_return_400_with_uniform_envelope(staff_client, payload, field):
    response = staff_client.post("/api/v1/create_customer/", payload, format="json")

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert field in error["details"]


@pytest.mark.django_db
def test_wrong_method_returns_405_with_envelope(staff_client):
    response = staff_client.get("/api/v1/create_customer/")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"
