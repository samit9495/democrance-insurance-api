"""Phase 1: custom User model (foundation for REQ-P4-2).

Email is the login identifier, roles discriminate principals, and the manager
enforces the invariants a custom user must hold from the first migration.
"""

import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_create_user_normalises_email_and_hashes_password():
    user = get_user_model().objects.create_user(email="Ben@Example.COM", password="s3cret!")

    assert user.email == "Ben@example.com"
    assert user.password != "s3cret!"
    assert user.check_password("s3cret!")


@pytest.mark.django_db
def test_create_user_without_email_raises():
    with pytest.raises(ValueError):
        get_user_model().objects.create_user(email="", password="x")


@pytest.mark.django_db
def test_default_role_is_customer():
    user = get_user_model().objects.create_user(email="c@example.com", password="x")

    assert user.role == "customer"


@pytest.mark.django_db
def test_create_superuser_sets_staff_and_superuser_flags():
    admin = get_user_model().objects.create_superuser(email="a@example.com", password="x")

    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.role == "staff"


def test_str_returns_email():
    user = get_user_model()(email="s@example.com")

    assert str(user) == "s@example.com"
