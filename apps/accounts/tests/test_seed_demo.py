"""Phase 9: the seed_demo command creates demo principals idempotently."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.customers.models import Customer

pytestmark = pytest.mark.django_db


def test_seed_demo_creates_principals_and_a_linked_customer():
    call_command("seed_demo")

    User = get_user_model()
    assert User.objects.filter(email="staff@demo.local", role="staff").exists()
    assert User.objects.filter(email="agent@demo.local", role="agent").exists()
    customer = Customer.objects.get(email="customer@demo.local")
    assert customer.user.email == "customer@demo.local"


def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")

    User = get_user_model()
    assert User.objects.filter(email__endswith="@demo.local").count() == 3
    assert Customer.objects.filter(email="customer@demo.local").count() == 1
