"""Phase 8: customer search (Part 3, REQUIREMENTS 8.2, D8).

Partial case-insensitive names, free-text q, dob in both formats, filter by held
policy type, AND semantics, and an empty (not 404) result when nothing matches.
"""

import datetime

import pytest

pytestmark = pytest.mark.django_db


@pytest.fixture
def stokes(customer_factory):
    return customer_factory(first_name="Ben", last_name="Stokes", dob=datetime.date(1991, 6, 25))


@pytest.fixture
def root(customer_factory):
    return customer_factory(first_name="Joe", last_name="Root", dob=datetime.date(1990, 12, 30))


def _ids(response):
    return {row["id"] for row in response.json()["results"]}


def test_partial_case_insensitive_surname(staff_client, stokes, root):
    response = staff_client.get("/api/v1/customers/?last_name=STOK")

    assert response.status_code == 200
    assert _ids(response) == {stokes.id}


def test_partial_first_name(staff_client, stokes, root):
    response = staff_client.get("/api/v1/customers/?first_name=jo")

    assert _ids(response) == {root.id}


def test_free_text_q_spans_either_name(staff_client, stokes, root):
    assert _ids(staff_client.get("/api/v1/customers/?q=stok")) == {stokes.id}
    assert _ids(staff_client.get("/api/v1/customers/?q=root")) == {root.id}


@pytest.mark.parametrize("dob", ["25-06-1991", "1991-06-25"])
def test_dob_accepts_both_formats(staff_client, stokes, root, dob):
    response = staff_client.get(f"/api/v1/customers/?dob={dob}")

    assert _ids(response) == {stokes.id}


def test_filter_by_held_policy_type(staff_client, stokes, root):
    from apps.policies import services
    from apps.products.models import ProductType

    pa = ProductType.objects.get(code="personal-accident")
    services.create_quote(customer=stokes, product=pa, as_of=datetime.date(2026, 8, 13))

    response = staff_client.get("/api/v1/customers/?policy_type=personal-accident")

    assert _ids(response) == {stokes.id}


def test_filters_combine_with_and(staff_client, stokes, root):
    # first_name matches Ben but last_name Root does not -> no rows.
    response = staff_client.get("/api/v1/customers/?first_name=ben&last_name=root")

    assert _ids(response) == set()


def test_no_matches_is_an_empty_page_not_404(staff_client, stokes):
    response = staff_client.get("/api/v1/customers/?q=zzzznothing")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["results"] == []
