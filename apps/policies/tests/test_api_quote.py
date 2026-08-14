"""Phase 6: the overloaded POST /api/v1/quote/ dispatcher and its REST aliases.

These replay diagram steps 2-4 verbatim (create with customer_id+type, accept
with status "accepted", pay with status "active"), prove premium is server-only,
and prove the RPC path and REST aliases agree across both slash spellings
(ADR-0002, ADR-0004).
"""

import datetime

import pytest
import time_machine

from apps.policies.state_machine import State

TODAY = datetime.date(2026, 8, 13)
PA = "personal-accident"


@pytest.fixture
def customer(customer_factory):
    # dob 25-06-1991 -> age 35 at the pinned clock, landing in band 31-40 (rate 1.00).
    return customer_factory(first_name="Ben", last_name="Stokes", dob=datetime.date(1991, 6, 25))


@time_machine.travel(TODAY)
@pytest.mark.django_db
def test_create_quote_replays_diagram_step_2(staff_client, customer):
    response = staff_client.post(
        "/api/v1/quote/", {"customer_id": customer.id, "type": PA}, format="json"
    )

    assert response.status_code == 201
    body = response.json()
    assert body["customer_id"] == customer.id
    assert body["type"] == PA
    assert body["state"] == State.QUOTED
    assert body["premium"] == "200.00"
    assert body["cover"] == "200000.00"
    assert body["rated_age"] == 35


@time_machine.travel(TODAY)
@pytest.mark.django_db
def test_dispatch_replays_diagram_steps_2_to_4(staff_client, customer):
    created = staff_client.post(
        "/api/v1/quote/", {"customer_id": customer.id, "type": PA}, format="json"
    ).json()
    quote_id = created["id"]

    accepted = staff_client.post(
        "/api/v1/quote/", {"quote_id": quote_id, "status": "accepted"}, format="json"
    )
    assert accepted.status_code == 200
    assert accepted.json()["state"] == State.ACCEPTED

    paid = staff_client.post(
        "/api/v1/quote/", {"quote_id": quote_id, "status": "active"}, format="json"
    )
    assert paid.status_code == 200
    body = paid.json()
    assert body["state"] == State.ACTIVE
    assert body["payment"] is not None
    assert body["payment"]["status"] == "succeeded"


@time_machine.travel(TODAY)
@pytest.mark.django_db
def test_invoice_payment_method_is_honoured(staff_client, customer):
    created = staff_client.post(
        "/api/v1/quote/", {"customer_id": customer.id, "type": PA}, format="json"
    ).json()
    quote_id = created["id"]
    staff_client.post("/api/v1/quote/", {"quote_id": quote_id, "status": "accepted"}, format="json")

    paid = staff_client.post(
        "/api/v1/quote/",
        {"quote_id": quote_id, "status": "active", "payment_method": "invoice"},
        format="json",
    )
    body = paid.json()
    assert body["state"] == State.ACTIVE
    assert body["payment"]["method"] == "invoice"
    assert body["payment"]["status"] == "pending"


@time_machine.travel(TODAY)
@pytest.mark.django_db
def test_ambiguous_payload_is_a_helpful_400(staff_client, customer):
    response = staff_client.post(
        "/api/v1/quote/",
        {"customer_id": customer.id, "type": PA, "quote_id": 1, "status": "accepted"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.django_db
def test_unrecognised_payload_is_a_helpful_400(staff_client):
    response = staff_client.post("/api/v1/quote/", {"foo": "bar"}, format="json")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.django_db
def test_unsupported_status_is_400(staff_client):
    response = staff_client.post(
        "/api/v1/quote/", {"quote_id": 1, "status": "frozen"}, format="json"
    )

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "status" in error["details"]


@time_machine.travel(TODAY)
@pytest.mark.django_db
def test_client_supplied_premium_is_rejected(staff_client, customer):
    response = staff_client.post(
        "/api/v1/quote/",
        {"customer_id": customer.id, "type": PA, "premium": "1.00"},
        format="json",
    )

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "premium" in error["details"]


@time_machine.travel(TODAY)
@pytest.mark.django_db
def test_cover_outside_limits_is_400(staff_client, customer):
    response = staff_client.post(
        "/api/v1/quote/",
        {"customer_id": customer.id, "type": PA, "cover": "999999999.00"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.django_db
def test_unknown_customer_is_404(staff_client):
    response = staff_client.post(
        "/api/v1/quote/", {"customer_id": 999999, "type": PA}, format="json"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.django_db
def test_unknown_product_is_404(staff_client, customer):
    response = staff_client.post(
        "/api/v1/quote/", {"customer_id": customer.id, "type": "no-such-product"}, format="json"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.django_db
def test_unknown_quote_is_404(staff_client):
    response = staff_client.post(
        "/api/v1/quote/", {"quote_id": 999999, "status": "accepted"}, format="json"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@time_machine.travel(TODAY)
@pytest.mark.django_db
def test_paying_an_unaccepted_quote_is_409(staff_client, customer):
    created = staff_client.post(
        "/api/v1/quote/", {"customer_id": customer.id, "type": PA}, format="json"
    ).json()

    response = staff_client.post(
        "/api/v1/quote/", {"quote_id": created["id"], "status": "active"}, format="json"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_state_transition"


@time_machine.travel(TODAY)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "create_path",
    ["/api/v1/quote/", "/api/v1/quote", "/api/v1/quotes/", "/api/v1/quotes"],
)
def test_create_parity_across_aliases_and_slashes(staff_client, customer, create_path):
    response = staff_client.post(
        create_path, {"customer_id": customer.id, "type": PA}, format="json"
    )

    assert response.status_code == 201
    body = response.json()
    assert body["state"] == State.QUOTED
    assert body["premium"] == "200.00"
    assert body["type"] == PA


@time_machine.travel(TODAY)
@pytest.mark.django_db
def test_rest_aliases_accept_and_pay_match_the_rpc_path(staff_client, customer):
    # Two independent quotes taken to 'active' by the two different route styles.
    def quote_id_via_rpc():
        return staff_client.post(
            "/api/v1/quote/", {"customer_id": customer.id, "type": PA}, format="json"
        ).json()["id"]

    rpc_id = quote_id_via_rpc()
    staff_client.post("/api/v1/quote/", {"quote_id": rpc_id, "status": "accepted"}, format="json")
    rpc_paid = staff_client.post(
        "/api/v1/quote/", {"quote_id": rpc_id, "status": "active"}, format="json"
    ).json()

    rest_id = quote_id_via_rpc()
    accept = staff_client.post(f"/api/v1/quotes/{rest_id}/accept/", {}, format="json")
    assert accept.status_code == 200
    assert accept.json()["state"] == State.ACCEPTED
    rest_paid = staff_client.post(f"/api/v1/quotes/{rest_id}/pay/", {}, format="json").json()

    assert rpc_paid["state"] == rest_paid["state"] == State.ACTIVE
    assert rpc_paid["premium"] == rest_paid["premium"]
    assert rpc_paid["payment"]["status"] == rest_paid["payment"]["status"] == "succeeded"
