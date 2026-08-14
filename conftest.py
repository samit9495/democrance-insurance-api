"""Root conftest so shared fixtures reach every test tree (apps/ and tests/).

Auth-aware client fixtures exist from Phase 2 even though authentication is not
enforced until Phase 9. When JWT lands, only these fixtures change — the test
bodies that use them do not (MASTER-PLAN 1.2).

Factory imports are deferred into the fixtures because this module is imported
before pytest-django has configured the app registry.
"""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def anon_client() -> APIClient:
    """An unauthenticated API client."""
    return APIClient()


@pytest.fixture
def staff_user(db):
    from apps.accounts.tests.factories import UserFactory

    return UserFactory(role="staff", is_staff=True)


@pytest.fixture
def agent_user(db):
    from apps.accounts.tests.factories import UserFactory

    return UserFactory(role="agent")


@pytest.fixture
def staff_client(staff_user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=staff_user)
    return client


@pytest.fixture
def agent_client(agent_user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=agent_user)
    return client


@pytest.fixture
def customer_client(db):
    """Return a factory that builds a client authenticated as a customer's own
    principal, linked to the given Customer record."""
    from apps.accounts.tests.factories import UserFactory

    def _make(customer) -> APIClient:
        user = UserFactory(role="customer")
        customer.user = user
        customer.save(update_fields=["user"])
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _make


@pytest.fixture
def customer_factory():
    from apps.customers.tests.factories import CustomerFactory

    return CustomerFactory


@pytest.fixture
def user_factory():
    from apps.accounts.tests.factories import UserFactory

    return UserFactory
