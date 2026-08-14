"""Factories for products."""

import datetime
from decimal import Decimal

import factory

from apps.products.models import ProductType, RatingRule


class ProductTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductType
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"product-{n}")
    name = factory.LazyAttribute(lambda o: o.code.title())
    is_active = True
    default_cover = Decimal("200000.00")
    min_cover = Decimal("1000.00")
    max_cover = Decimal("1000000.00")
    min_age = 18
    max_age = 100


class RatingRuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RatingRule

    product = factory.SubFactory(ProductTypeFactory)
    age_band_min = 18
    age_band_max = 100
    rate_per_1000_cover = Decimal("1.0000")
    loading_factor = Decimal("1.0000")
    min_premium = Decimal("50.00")
    valid_from = datetime.date(2020, 1, 1)
    valid_to = None
    is_active = True
