"""Phase 3: the rating engine (REQ-P2-3, domain-invariants — 100% coverage).

A bug here costs money, so every branch is exercised: the brief's own example,
band boundaries, the min-premium clamp, ROUND_HALF_UP, date-versioned selection,
and each rejection path.
"""

import datetime
from decimal import Decimal

import pytest

from apps.products.rating import RatingError, calculate_premium
from apps.products.tests.factories import ProductTypeFactory, RatingRuleFactory

AS_OF = datetime.date(2026, 8, 13)

BANDS = [
    (18, 25, "1.30"),
    (26, 30, "1.15"),
    (31, 40, "1.00"),
    (41, 50, "1.40"),
    (51, 60, "2.00"),
    (61, 70, "3.10"),
]


@pytest.fixture
def pa_product(db):
    # A distinct code so this fixture is independent of the seeded catalogue.
    product = ProductTypeFactory(
        code="pa-under-test",
        min_age=18,
        max_age=70,
        min_cover=Decimal("1000.00"),
        max_cover=Decimal("1000000.00"),
    )
    for lo, hi, rate in BANDS:
        RatingRuleFactory(
            product=product,
            age_band_min=lo,
            age_band_max=hi,
            rate_per_1000_cover=Decimal(rate),
            min_premium=Decimal("50.00"),
        )
    return product


@pytest.mark.django_db
def test_brief_example_prices_at_200(pa_product):
    premium = calculate_premium(pa_product, age=35, cover=Decimal("200000.00"), as_of=AS_OF)

    assert premium == Decimal("200.00")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (18, "130.00"),
        (25, "130.00"),
        (26, "115.00"),
        (30, "115.00"),
        (31, "100.00"),
        (40, "100.00"),
        (41, "140.00"),
        (70, "310.00"),
    ],
)
def test_band_boundaries_select_the_right_rate(pa_product, age, expected):
    premium = calculate_premium(pa_product, age=age, cover=Decimal("100000.00"), as_of=AS_OF)

    assert premium == Decimal(expected)


@pytest.mark.django_db
@pytest.mark.parametrize("age", [17, 71])
def test_ages_outside_product_eligibility_are_rejected(pa_product, age):
    with pytest.raises(RatingError):
        calculate_premium(pa_product, age=age, cover=Decimal("100000.00"), as_of=AS_OF)


@pytest.mark.django_db
def test_min_premium_is_applied_as_a_floor(pa_product):
    premium = calculate_premium(pa_product, age=31, cover=Decimal("1000.00"), as_of=AS_OF)

    assert premium == Decimal("50.00")


@pytest.mark.django_db
def test_cover_outside_limits_is_rejected(pa_product):
    with pytest.raises(RatingError):
        calculate_premium(pa_product, age=35, cover=Decimal("999.00"), as_of=AS_OF)
    with pytest.raises(RatingError):
        calculate_premium(pa_product, age=35, cover=Decimal("2000000.00"), as_of=AS_OF)


@pytest.mark.django_db
def test_inactive_product_is_rejected():
    product = ProductTypeFactory(is_active=False, min_cover=Decimal("0.00"))
    RatingRuleFactory(product=product)

    with pytest.raises(RatingError):
        calculate_premium(product, age=35, cover=Decimal("100000.00"), as_of=AS_OF)


@pytest.mark.django_db
def test_missing_band_within_eligibility_is_rejected():
    product = ProductTypeFactory(min_age=0, max_age=200, min_cover=Decimal("0.00"))
    RatingRuleFactory(product=product, age_band_min=18, age_band_max=25)
    RatingRuleFactory(product=product, age_band_min=31, age_band_max=40)

    with pytest.raises(RatingError):  # age 28 falls in the 26-30 gap
        calculate_premium(product, age=28, cover=Decimal("100000.00"), as_of=AS_OF)


@pytest.mark.django_db
def test_rounding_is_half_up_not_bankers():
    product = ProductTypeFactory(min_age=0, max_age=200, min_cover=Decimal("0.00"))
    RatingRuleFactory(
        product=product,
        age_band_min=0,
        age_band_max=200,
        rate_per_1000_cover=Decimal("1.0000"),
        min_premium=Decimal("0.01"),
    )

    # 10005 / 1000 * 1 = 10.005 -> 10.01 half-up (would be 10.00 under banker's).
    premium = calculate_premium(product, age=30, cover=Decimal("10005.00"), as_of=AS_OF)

    assert premium == Decimal("10.01")


@pytest.mark.django_db
def test_date_versioned_rule_selection():
    product = ProductTypeFactory(min_age=0, max_age=200, min_cover=Decimal("0.00"))
    RatingRuleFactory(
        product=product,
        age_band_min=0,
        age_band_max=200,
        rate_per_1000_cover=Decimal("2.0000"),
        valid_from=datetime.date(2020, 1, 1),
        valid_to=datetime.date(2022, 12, 31),
    )
    RatingRuleFactory(
        product=product,
        age_band_min=0,
        age_band_max=200,
        rate_per_1000_cover=Decimal("1.0000"),
        valid_from=datetime.date(2023, 1, 1),
        valid_to=None,
    )

    cover = Decimal("100000.00")
    old = calculate_premium(product, age=30, cover=cover, as_of=datetime.date(2021, 6, 1))
    new = calculate_premium(product, age=30, cover=cover, as_of=datetime.date(2024, 6, 1))

    assert old == Decimal("200.00")
    assert new == Decimal("100.00")
