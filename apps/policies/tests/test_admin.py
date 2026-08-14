"""Phase 10: the policy admin surfaces the customer link, keeps transitions
read-only, and routes its actions through the service layer (REQUIREMENTS 10)."""

import datetime

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.policies import services
from apps.policies.admin import PolicyAdmin
from apps.policies.models import Policy, PolicyStateTransition
from apps.policies.state_machine import State
from apps.products.models import ProductType

pytestmark = pytest.mark.django_db
TODAY = datetime.date(2026, 8, 13)


@pytest.fixture
def admin_client_(client):
    admin_user = get_user_model().objects.create_superuser(email="admin@example.com", password="pw")
    client.force_login(admin_user)
    return client


@pytest.fixture
def quote(customer_factory):
    customer = customer_factory(
        first_name="Ben", last_name="Stokes", dob=datetime.date(1991, 6, 25)
    )
    product = ProductType.objects.get(code="personal-accident")
    return services.create_quote(customer=customer, product=product, as_of=TODAY)


def test_changelist_shows_the_linked_customer(admin_client_, quote):
    response = admin_client_.get(reverse("admin:policies_policy_changelist"))

    assert response.status_code == 200
    assert b"Stokes" in response.content


def test_state_is_not_directly_editable():
    assert "state" in admin.site._registry[Policy].readonly_fields


def test_transition_inline_is_read_only():
    inline = PolicyAdmin.inlines[0]
    assert inline.has_add_permission(inline, request=None) is False
    assert set(inline.readonly_fields) == set(inline.fields)


def test_accept_action_goes_through_the_service(admin_client_, quote):
    admin_client_.post(
        reverse("admin:policies_policy_changelist"),
        {"action": "accept_selected_quotes", "_selected_action": [quote.pk]},
    )

    quote.refresh_from_db()
    assert quote.state == State.ACCEPTED
    last = quote.transitions.latest("id")
    assert last.to_state == State.ACCEPTED
    assert last.source == "admin"


def test_bind_action_binds_and_audits_as_admin(admin_client_, quote):
    services.accept_quote(policy=quote)

    admin_client_.post(
        reverse("admin:policies_policy_changelist"),
        {"action": "bind_selected_policies", "_selected_action": [quote.pk]},
    )

    quote.refresh_from_db()
    assert quote.state == State.ACTIVE
    activation = quote.transitions.get(to_state=State.ACTIVE)
    assert activation.source == "admin"


def test_transition_admin_is_read_only():
    model_admin = admin.site._registry[PolicyStateTransition]
    assert model_admin.has_add_permission(request=None) is False
    assert model_admin.has_change_permission(request=None) is False
    assert model_admin.has_delete_permission(request=None) is False
