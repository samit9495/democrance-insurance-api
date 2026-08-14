"""Phase 3: ProductType and RatingRule invariants (REQUIREMENTS 6.3/6.4)."""

import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.products.models import RatingRule
from apps.products.tests.factories import ProductTypeFactory, RatingRuleFactory


@pytest.mark.django_db
def test_check_constraint_rejects_inverted_age_band():
    product = ProductTypeFactory()

    with pytest.raises(IntegrityError), transaction.atomic():
        RatingRule.objects.create(
            product=product,
            age_band_min=40,
            age_band_max=30,
            rate_per_1000_cover=Decimal("1.0000"),
            min_premium=Decimal("50.00"),
            valid_from=datetime.date(2020, 1, 1),
        )


@pytest.mark.django_db
def test_overlapping_active_bands_are_rejected():
    product = ProductTypeFactory()
    RatingRuleFactory(product=product, age_band_min=18, age_band_max=30)

    clashing = RatingRule(
        product=product,
        age_band_min=25,
        age_band_max=40,
        rate_per_1000_cover=Decimal("1.0000"),
        min_premium=Decimal("50.00"),
        valid_from=datetime.date(2020, 1, 1),
    )

    with pytest.raises(ValidationError):
        clashing.full_clean()


@pytest.mark.django_db
def test_versioned_bands_in_disjoint_windows_do_not_clash():
    product = ProductTypeFactory()
    RatingRuleFactory(
        product=product,
        age_band_min=18,
        age_band_max=30,
        valid_from=datetime.date(2020, 1, 1),
        valid_to=datetime.date(2025, 12, 31),
    )

    superseding = RatingRule(
        product=product,
        age_band_min=18,
        age_band_max=30,
        rate_per_1000_cover=Decimal("1.5000"),
        min_premium=Decimal("50.00"),
        valid_from=datetime.date(2026, 1, 1),
    )

    superseding.full_clean()  # must not raise


@pytest.mark.django_db
def test_str_methods():
    product = ProductTypeFactory(code="personal-accident")
    rule = RatingRuleFactory(product=product, age_band_min=31, age_band_max=40)

    assert str(product) == "personal-accident"
    assert "31" in str(rule) and "40" in str(rule)
