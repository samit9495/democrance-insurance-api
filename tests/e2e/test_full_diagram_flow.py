"""End-to-end replay of the sequence diagram, over HTTP, from a cold database.

This is the executable form of ``docs/sequence-diagram.png``: a single test
walks the seven steps a reviewer would run by hand and asserts the observable
result of each, finishing on the exact four-entry transition narrative. If this
passes, the diagram is satisfied end-to-end.
"""

import datetime

import pytest
import time_machine

from apps.policies.state_machine import State

TODAY = datetime.date(2026, 8, 13)
PA = "personal-accident"


@time_machine.travel(TODAY)
@pytest.mark.django_db
def test_seven_step_diagram_flow(anon_client):
    # Step 1 - create the customer (brief's literal example payload).
    created = anon_client.post(
        "/api/v1/create_customer/",
        {"first_name": "Ben", "last_name": "Stokes", "dob": "25-06-1991"},
        format="json",
    )
    assert created.status_code == 201
    customer_id = created.json()["id"]

    # Step 2 - quote: premium is priced server-side at 200.00.
    quoted = anon_client.post(
        "/api/v1/quote/", {"customer_id": customer_id, "type": PA}, format="json"
    )
    assert quoted.status_code == 201
    quote = quoted.json()
    quote_id = quote["id"]
    assert quote["state"] == State.QUOTED
    assert quote["premium"] == "200.00"

    # Step 3 - accept.
    accepted = anon_client.post(
        "/api/v1/quote/", {"quote_id": quote_id, "status": "accepted"}, format="json"
    )
    assert accepted.status_code == 200
    assert accepted.json()["state"] == State.ACCEPTED

    # Step 4 - pay: the policy binds and a succeeded payment is attached.
    paid = anon_client.post(
        "/api/v1/quote/", {"quote_id": quote_id, "status": "active"}, format="json"
    )
    assert paid.status_code == 200
    paid_body = paid.json()
    assert paid_body["state"] == State.ACTIVE
    assert paid_body["payment"]["status"] == "succeeded"

    # Step 5 - list policies for the customer.
    listing = anon_client.get(f"/api/v1/policies/?customer_id={customer_id}")
    assert listing.status_code == 200
    listed = listing.json()
    assert listed["count"] == 1
    assert listed["results"][0]["id"] == quote_id

    # Step 6 - policy detail carries the priced premium and the payment.
    detail = anon_client.get(f"/api/v1/policies/{quote_id}/")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["premium"] == "200.00"
    assert detail_body["payment"]["status"] == "succeeded"

    # Step 7 - the history is the full, ordered narrative.
    history = anon_client.get(f"/api/v1/policies/{quote_id}/history/")
    assert history.status_code == 200
    steps = [(t["from_state"], t["to_state"]) for t in history.json()["transitions"]]
    assert steps == [
        (None, State.NEW),
        (State.NEW, State.QUOTED),
        (State.QUOTED, State.ACCEPTED),
        (State.ACCEPTED, State.ACTIVE),
    ]


@pytest.mark.django_db
def test_every_response_echoes_a_request_id(anon_client):
    # ENH-13: the middleware honours an inbound id and stamps it on the response.
    response = anon_client.get("/healthz/", HTTP_X_REQUEST_ID="trace-abc-123")
    assert response.headers["X-Request-ID"] == "trace-abc-123"


@pytest.mark.django_db
def test_request_id_is_minted_when_absent(anon_client):
    response = anon_client.get("/healthz/")
    assert response.headers.get("X-Request-ID")
