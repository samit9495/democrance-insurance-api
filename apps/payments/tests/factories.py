"""Factory for payments. Rows are built directly; the card/invoice branching and
policy binding are exercised through the service, not this factory."""

from decimal import Decimal

import factory

from apps.payments.models import Payment
from apps.policies.tests.factories import PolicyFactory


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    policy = factory.SubFactory(PolicyFactory)
    amount = Decimal("200.00")
    currency = "AED"
    method = Payment.Method.CARD
    status = Payment.Status.SUCCEEDED
