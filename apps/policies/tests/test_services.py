"""Phase 4: quote/policy services (REQ-P2-2/5/7, domain-invariants).

Services are the only mutator of Policy.state, and every mutation writes a
transition in the same transaction. These tests drive the whole lifecycle with
no HTTP involved.
"""

import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.customers.tests.factories import CustomerFactory
from apps.policies import services
from apps.policies.exceptions import InvalidStateTransition, QuoteExpired
from apps.policies.state_machine import State
from apps.products.tests.factories import ProductTypeFactory, RatingRuleFactory

AS_OF = datetime.date(2026, 8, 13)


@pytest.fixture
def product_pa(db):
    product = ProductTypeFactory(
        min_age=18,
        max_age=70,
        min_cover=Decimal("1000.00"),
        max_cover=Decimal("1000000.00"),
        default_cover=Decimal("200000.00"),
        currency="AED",
    )
    RatingRuleFactory(
        product=product,
        age_band_min=31,
        age_band_max=40,
        rate_per_1000_cover=Decimal("1.0000"),
        min_premium=Decimal("50.00"),
    )
    return product


@pytest.fixture
def customer_35(db):
    return CustomerFactory(dob=datetime.date(1991, 6, 25))


def _states(policy):
    return [(t.from_state, t.to_state) for t in policy.transitions.all()]


@pytest.mark.django_db
def test_create_quote_logs_new_then_quoted_and_prices(product_pa, customer_35):
    policy = services.create_quote(
        customer=customer_35, product=product_pa, cover=Decimal("200000.00"), as_of=AS_OF
    )

    assert policy.state == State.QUOTED
    assert policy.premium == Decimal("200.00")
    assert policy.rated_age == 35
    assert policy.quote_expires_at is not None
    assert _states(policy) == [(None, State.NEW), (State.NEW, State.QUOTED)]


@pytest.mark.django_db
def test_create_quote_defaults_cover_to_product_default(product_pa, customer_35):
    policy = services.create_quote(customer=customer_35, product=product_pa, as_of=AS_OF)

    assert policy.cover == product_pa.default_cover


@pytest.mark.django_db
def test_accept_quote_sets_accepted(product_pa, customer_35):
    policy = services.create_quote(customer=customer_35, product=product_pa, as_of=AS_OF)

    accepted = services.accept_quote(policy=policy)

    assert accepted.state == State.ACCEPTED
    assert accepted.accepted_at is not None
    assert _states(accepted)[-1] == (State.QUOTED, State.ACCEPTED)


@pytest.mark.django_db
def test_accepting_an_expired_quote_is_refused(product_pa, customer_35):
    policy = services.create_quote(customer=customer_35, product=product_pa, as_of=AS_OF)
    policy.quote_expires_at = timezone.now() - datetime.timedelta(days=1)
    policy.save(update_fields=["quote_expires_at"])

    with pytest.raises(QuoteExpired):
        services.accept_quote(policy=policy)

    policy.refresh_from_db()
    assert policy.state == State.QUOTED
    assert policy.transitions.count() == 2


@pytest.mark.django_db
def test_activate_requires_accepted_and_writes_no_row_on_failure(product_pa, customer_35):
    policy = services.create_quote(customer=customer_35, product=product_pa, as_of=AS_OF)

    with pytest.raises(InvalidStateTransition):
        services.activate_policy(policy=policy)

    policy.refresh_from_db()
    assert policy.state == State.QUOTED
    assert policy.transitions.count() == 2  # no accepted->active row written


@pytest.mark.django_db
def test_full_lifecycle_records_the_whole_narrative(product_pa, customer_35):
    policy = services.create_quote(customer=customer_35, product=product_pa, as_of=AS_OF)
    services.accept_quote(policy=policy)
    active = services.activate_policy(policy=policy)

    assert active.state == State.ACTIVE
    assert active.activated_at is not None
    assert _states(active) == [
        (None, State.NEW),
        (State.NEW, State.QUOTED),
        (State.QUOTED, State.ACCEPTED),
        (State.ACCEPTED, State.ACTIVE),
    ]


@pytest.mark.django_db
def test_activating_twice_binds_only_once(product_pa, customer_35):
    policy = services.create_quote(customer=customer_35, product=product_pa, as_of=AS_OF)
    services.accept_quote(policy=policy)
    services.activate_policy(policy=policy)

    with pytest.raises(InvalidStateTransition):
        services.activate_policy(policy=policy)

    policy.refresh_from_db()
    assert policy.state == State.ACTIVE
    assert [t for _, t in _states(policy)].count(State.ACTIVE) == 1
