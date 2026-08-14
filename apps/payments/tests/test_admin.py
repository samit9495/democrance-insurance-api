"""The payment admin is a read-only ledger: it lists but never edits receipts."""

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.payments.models import Payment
from apps.payments.tests.factories import PaymentFactory


@pytest.fixture
def admin_client_(client):
    admin_user = get_user_model().objects.create_superuser(email="admin@example.com", password="pw")
    client.force_login(admin_user)
    return client


@pytest.mark.django_db
def test_payment_is_listed_in_admin(admin_client_):
    PaymentFactory()
    url = reverse("admin:payments_payment_changelist")

    assert admin_client_.get(url).status_code == 200


def test_admin_forbids_mutation():
    model_admin = admin.site._registry[Payment]

    assert model_admin.has_add_permission(request=None) is False
    assert model_admin.has_change_permission(request=None) is False
    assert model_admin.has_delete_permission(request=None) is False
