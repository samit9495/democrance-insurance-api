"""Phase 7: list, detail and history (diagram steps 5-7, REQ-P2-5, REQ-P3-4).

Covers customer_id filtering, newest-first pagination, absence of N+1 on the
list, the detail's nested customer + rating inputs + payment, a 404 on unknown
ids, and the exact four-entry history the brief draws.
"""

import datetime

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.payments.services import simulate_payment
from apps.policies import services
from apps.policies.state_machine import State
from apps.products.models import ProductType

TODAY = datetime.date(2026, 8, 13)
PA = "personal-accident"

pytestmark = pytest.mark.django_db


@pytest.fixture
def product():
    return ProductType.objects.get(code=PA)


def _quote(customer, product):
    return services.create_quote(customer=customer, product=product, as_of=TODAY)


def _active_policy(customer, product):
    policy = _quote(customer, product)
    services.accept_quote(policy=policy)
    simulate_payment(policy=policy, method="simulated_card")
    policy.refresh_from_db()
    return policy


def test_list_filters_by_customer_id(staff_client, customer_factory, product):
    mine = customer_factory(dob=datetime.date(1991, 6, 25))
    other = customer_factory(dob=datetime.date(1991, 6, 25))
    my_policy = _quote(mine, product)
    _quote(other, product)

    response = staff_client.get(f"/api/v1/policies/?customer_id={mine.id}")

    assert response.status_code == 200
    results = response.json()["results"]
    assert [row["id"] for row in results] == [my_policy.id]


def test_list_is_paginated_and_newest_first(staff_client, customer_factory, product):
    customer = customer_factory(dob=datetime.date(1991, 6, 25))
    first = _quote(customer, product)
    second = _quote(customer, product)

    body = staff_client.get(f"/api/v1/policies/?customer_id={customer.id}").json()

    assert set(body) == {"count", "next", "previous", "results"}
    assert [row["id"] for row in body["results"]] == [second.id, first.id]


def test_list_has_no_n_plus_one(staff_client, customer_factory, product):
    def query_count(n: int) -> int:
        customer = customer_factory(dob=datetime.date(1991, 6, 25))
        for _ in range(n):
            _active_policy(customer, product)
        with CaptureQueriesContext(connection) as ctx:
            staff_client.get(f"/api/v1/policies/?customer_id={customer.id}")
        return len(ctx.captured_queries)

    # Same number of queries for 2 rows as for 5 -> the query count is flat.
    assert query_count(2) == query_count(5)


def test_detail_includes_customer_rating_inputs_and_payment(
    staff_client, customer_factory, product
):
    customer = customer_factory(
        first_name="Ben", last_name="Stokes", dob=datetime.date(1991, 6, 25)
    )
    policy = _active_policy(customer, product)

    body = staff_client.get(f"/api/v1/policies/{policy.id}/").json()

    assert body["customer"]["first_name"] == "Ben"
    assert body["rated_age"] == 35
    assert body["rated_at"] is not None
    assert body["payment"]["status"] == "succeeded"


def test_detail_unknown_id_is_404(staff_client):
    response = staff_client.get("/api/v1/policies/999999/")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_history_returns_the_full_four_entry_narrative(staff_client, customer_factory, product):
    customer = customer_factory(dob=datetime.date(1991, 6, 25))
    policy = _active_policy(customer, product)

    body = staff_client.get(f"/api/v1/policies/{policy.id}/history/").json()

    assert body["policy_id"] == policy.id
    assert body["current_state"] == State.ACTIVE
    moves = [(t["from_state"], t["to_state"]) for t in body["transitions"]]
    assert moves == [
        (None, State.NEW),
        (State.NEW, State.QUOTED),
        (State.QUOTED, State.ACCEPTED),
        (State.ACCEPTED, State.ACTIVE),
    ]


def test_history_of_a_fresh_quote_shows_only_two_moves(staff_client, customer_factory, product):
    customer = customer_factory(dob=datetime.date(1991, 6, 25))
    policy = _quote(customer, product)

    body = staff_client.get(f"/api/v1/policies/{policy.id}/history/").json()

    moves = [(t["from_state"], t["to_state"]) for t in body["transitions"]]
    assert moves == [(None, State.NEW), (State.NEW, State.QUOTED)]


def test_policies_filter_by_type_and_state(staff_client, customer_factory, product):
    customer = customer_factory(dob=datetime.date(1991, 6, 25))
    quoted = _quote(customer, product)
    active = _active_policy(customer, product)

    quoted_only = staff_client.get("/api/v1/policies/?type=personal-accident&state=quoted").json()
    active_only = staff_client.get("/api/v1/policies/?type=personal-accident&state=active").json()

    assert [row["id"] for row in quoted_only["results"]] == [quoted.id]
    assert [row["id"] for row in active_only["results"]] == [active.id]


def test_policies_free_text_q_matches_customer_name(staff_client, customer_factory, product):
    stokes = customer_factory(first_name="Ben", last_name="Stokes", dob=datetime.date(1991, 6, 25))
    other = customer_factory(first_name="Joe", last_name="Root", dob=datetime.date(1990, 12, 30))
    mine = _quote(stokes, product)
    _quote(other, product)

    body = staff_client.get("/api/v1/policies/?q=stok").json()

    assert [row["id"] for row in body["results"]] == [mine.id]


def test_policies_empty_result_is_not_404(staff_client):
    response = staff_client.get("/api/v1/policies/?state=cancelled")

    assert response.status_code == 200
    assert response.json()["count"] == 0


@pytest.mark.parametrize(
    "path_template",
    [
        "/api/v1/policies/?customer_id={cid}",
        "/api/v1/policies/{pid}/",
        "/api/v1/policies/{pid}/history/",
    ],
)
def test_diagram_steps_5_to_7_paths_all_respond(
    staff_client, customer_factory, product, path_template
):
    customer = customer_factory(dob=datetime.date(1991, 6, 25))
    policy = _active_policy(customer, product)

    url = path_template.format(cid=customer.id, pid=policy.id)
    assert staff_client.get(url).status_code == 200
