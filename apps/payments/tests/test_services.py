"""simulate_payment: both brief payment paths, idempotency, and atomic binding.

The service is the only place a payment is created and the only non-quote path
that activates a policy, so these tests drive it to 100% (Phase 5 gate).
"""

import pytest

from apps.payments.exceptions import DuplicateRequest, PaymentNotAllowed
from apps.payments.models import Payment
from apps.payments.services import simulate_payment
from apps.policies.state_machine import State
from apps.policies.tests.factories import PolicyFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def accepted_policy():
    return PolicyFactory(state=State.ACCEPTED)


def test_card_payment_succeeds_and_binds(accepted_policy):
    payment = simulate_payment(policy=accepted_policy, method=Payment.Method.CARD)

    assert payment.status == Payment.Status.SUCCEEDED
    assert payment.settled_at is not None
    accepted_policy.refresh_from_db()
    assert accepted_policy.state == State.ACTIVE


def test_invoice_payment_is_pending_but_still_binds(accepted_policy):
    payment = simulate_payment(policy=accepted_policy, method=Payment.Method.INVOICE)

    assert payment.status == Payment.Status.PENDING
    assert payment.settled_at is None
    accepted_policy.refresh_from_db()
    assert accepted_policy.state == State.ACTIVE


def test_amount_and_currency_track_the_policy(accepted_policy):
    payment = simulate_payment(policy=accepted_policy, method=Payment.Method.CARD)

    assert payment.amount == accepted_policy.premium
    assert payment.currency == accepted_policy.currency


def test_activation_records_the_payment_reference(accepted_policy):
    payment = simulate_payment(policy=accepted_policy, method=Payment.Method.CARD)

    activation = accepted_policy.transitions.get(to_state=State.ACTIVE)
    assert activation.metadata["payment_reference"] == str(payment.reference)
    assert activation.metadata["method"] == Payment.Method.CARD


def test_payment_refused_unless_policy_is_accepted():
    quoted = PolicyFactory(state=State.QUOTED)

    with pytest.raises(PaymentNotAllowed):
        simulate_payment(policy=quoted, method=Payment.Method.CARD)

    quoted.refresh_from_db()
    assert quoted.state == State.QUOTED
    assert Payment.objects.count() == 0


def test_unsupported_method_is_rejected(accepted_policy):
    from rest_framework.exceptions import ValidationError

    with pytest.raises(ValidationError):
        simulate_payment(policy=accepted_policy, method="cheque")

    assert Payment.objects.count() == 0


def test_idempotent_replay_returns_the_same_payment(accepted_policy):
    first = simulate_payment(
        policy=accepted_policy, method=Payment.Method.CARD, idempotency_key="abc-123"
    )
    again = simulate_payment(
        policy=accepted_policy, method=Payment.Method.CARD, idempotency_key="abc-123"
    )

    assert again.pk == first.pk
    assert Payment.objects.count() == 1
    accepted_policy.refresh_from_db()
    assert accepted_policy.state == State.ACTIVE
    # Exactly one activation: the replay did not bind the policy a second time.
    assert accepted_policy.transitions.filter(to_state=State.ACTIVE).count() == 1


def test_same_key_with_a_different_body_conflicts(accepted_policy):
    simulate_payment(policy=accepted_policy, method=Payment.Method.CARD, idempotency_key="dup-1")

    with pytest.raises(DuplicateRequest):
        simulate_payment(
            policy=accepted_policy, method=Payment.Method.INVOICE, idempotency_key="dup-1"
        )

    assert Payment.objects.count() == 1
