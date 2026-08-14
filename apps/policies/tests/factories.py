"""Factories for policies. These build rows directly; lifecycle transitions go
through the service layer, not these factories."""

from decimal import Decimal

import factory

from apps.customers.tests.factories import CustomerFactory
from apps.policies.models import Policy, PolicyStateTransition
from apps.policies.state_machine import State
from apps.products.tests.factories import ProductTypeFactory


class PolicyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Policy

    customer = factory.SubFactory(CustomerFactory)
    product = factory.SubFactory(ProductTypeFactory)
    premium = Decimal("200.00")
    cover = Decimal("200000.00")
    currency = "AED"
    state = State.NEW


class PolicyStateTransitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PolicyStateTransition

    policy = factory.SubFactory(PolicyFactory)
    from_state = None
    to_state = State.NEW
    source = "system"
