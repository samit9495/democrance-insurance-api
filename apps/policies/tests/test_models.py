"""Phase 4: Policy and PolicyStateTransition invariants (REQUIREMENTS 6.5/6.6)."""

import pytest
from django.db.models import ProtectedError

from apps.policies.tests.factories import PolicyFactory, PolicyStateTransitionFactory


@pytest.mark.django_db
def test_transition_is_immutable_after_save():
    transition = PolicyStateTransitionFactory()

    transition.reason = "tampered"
    with pytest.raises(ValueError, match="immutable"):
        transition.save()


@pytest.mark.django_db
def test_customer_with_policies_cannot_be_deleted():
    policy = PolicyFactory()

    with pytest.raises(ProtectedError):
        policy.customer.delete()


@pytest.mark.django_db
def test_product_with_policies_cannot_be_deleted():
    policy = PolicyFactory()

    with pytest.raises(ProtectedError):
        policy.product.delete()


@pytest.mark.django_db
def test_quote_reference_is_generated_and_unique():
    first = PolicyFactory()
    second = PolicyFactory()

    assert first.quote_reference.startswith("QT-")
    assert first.quote_reference != second.quote_reference
