"""The custom User is registered in the admin with BaseUserAdmin-style password
management: passwords are set via the add form (hashed), shown as a read-only
hash on the change form, and changed through the dedicated set-password view.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.fixture
def admin_client_(client):
    admin = get_user_model().objects.create_superuser(email="admin@example.com", password="pw")
    client.force_login(admin)
    return client


@pytest.mark.django_db
def test_user_is_listed_and_searchable_by_email(admin_client_, user_factory):
    user_factory(email="ben@example.com", role="agent")
    user_factory(email="joe@example.com", role="customer")

    url = reverse("admin:accounts_user_changelist")
    response = admin_client_.get(url, {"q": "ben@example.com"})

    assert response.status_code == 200
    assert b"ben@example.com" in response.content
    assert b"joe@example.com" not in response.content


@pytest.mark.django_db
def test_change_page_shows_password_as_readonly_hash(admin_client_, user_factory):
    user = user_factory(email="ben@example.com")

    url = reverse("admin:accounts_user_change", args=[user.id])
    response = admin_client_.get(url)

    assert response.status_code == 200
    # The hallmark of BaseUserAdmin: the raw password is never editable; the
    # field renders a read-only hash with this help text.
    assert b"Raw passwords are not stored" in response.content


@pytest.mark.django_db
def test_add_form_creates_user_with_a_hashed_password(admin_client_):
    User = get_user_model()

    add_url = reverse("admin:accounts_user_add")
    assert admin_client_.get(add_url).status_code == 200

    response = admin_client_.post(
        add_url,
        {
            "email": "newbie@example.com",
            "role": "agent",
            "password1": "s3cret-pass-123",
            "password2": "s3cret-pass-123",
            "usable_password": "true",  # present only on Django >= 5.1; harmless otherwise
        },
    )

    assert response.status_code in (200, 302)
    user = User.objects.get(email="newbie@example.com")
    assert user.role == "agent"
    assert user.password != "s3cret-pass-123"  # stored hashed, not in clear
    assert user.check_password("s3cret-pass-123")  # and verifiable


@pytest.mark.django_db
def test_dedicated_set_password_view_renders(admin_client_, user_factory):
    user = user_factory(email="ben@example.com")

    # BaseUserAdmin registers this view under a fixed name (not app-scoped).
    url = reverse("admin:auth_user_password_change", args=[user.id])
    response = admin_client_.get(url)

    assert response.status_code == 200
