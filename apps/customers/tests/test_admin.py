"""Phase 2: Customer admin (REQ-P1-6 — customer visible and correct in admin)."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.customers.tests.factories import CustomerFactory


@pytest.fixture
def admin_client_(client):
    admin = get_user_model().objects.create_superuser(email="admin@example.com", password="pw")
    client.force_login(admin)
    return client


@pytest.mark.django_db
def test_customer_is_listed_in_admin(admin_client_):
    CustomerFactory(first_name="Ben", last_name="Stokes")

    url = reverse("admin:customers_customer_changelist")
    response = admin_client_.get(url)

    assert response.status_code == 200
    assert b"Stokes" in response.content


@pytest.mark.django_db
def test_customer_is_searchable_by_surname(admin_client_):
    CustomerFactory(first_name="Ben", last_name="Stokes")
    CustomerFactory(first_name="Joe", last_name="Root")

    url = reverse("admin:customers_customer_changelist")
    response = admin_client_.get(url, {"q": "Stokes"})

    assert response.status_code == 200
    assert b"Stokes" in response.content
    assert b"Root" not in response.content


@pytest.mark.django_db
def test_customer_change_page_renders(admin_client_):
    customer = CustomerFactory(first_name="Ben", last_name="Stokes")

    url = reverse("admin:customers_customer_change", args=[customer.id])
    response = admin_client_.get(url)

    assert response.status_code == 200
