"""Factories for Customer."""

import datetime

import factory

from apps.customers.models import Customer


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    first_name = factory.Sequence(lambda n: f"First{n}")
    last_name = factory.Sequence(lambda n: f"Last{n}")
    dob = datetime.date(1991, 6, 25)
