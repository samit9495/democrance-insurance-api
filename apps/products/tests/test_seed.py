"""Phase 3: the seed migration lets a fresh clone reproduce the brief exactly."""

import datetime
from decimal import Decimal

import pytest

from apps.products.models import ProductType
from apps.products.rating import calculate_premium


@pytest.mark.django_db
def test_seed_creates_the_catalogue():
    codes = set(ProductType.objects.values_list("code", flat=True))

    assert {"personal-accident", "travel"} <= codes


@pytest.mark.django_db
def test_seeded_personal_accident_reproduces_brief_premium():
    product = ProductType.objects.get(code="personal-accident")

    premium = calculate_premium(
        product, age=35, cover=Decimal("200000.00"), as_of=datetime.date(2026, 8, 13)
    )

    assert premium == Decimal("200.00")
