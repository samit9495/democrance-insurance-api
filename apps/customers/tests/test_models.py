"""Phase 2: Customer model (REQUIREMENTS 6.2).

Age arithmetic must be exact at the birthday boundary and for leap-year births,
and an insurer cannot rate outside its filed age bands, so out-of-range and
future dates of birth are rejected.
"""

import datetime

import pytest
import time_machine
from django.core.exceptions import ValidationError

from apps.customers.models import Customer

TODAY = datetime.date(2026, 8, 13)


@pytest.mark.parametrize(
    ("dob", "as_of", "expected"),
    [
        (datetime.date(2000, 8, 13), datetime.date(2026, 8, 13), 26),  # on the birthday
        (datetime.date(2000, 8, 14), datetime.date(2026, 8, 13), 25),  # day before
        (datetime.date(2000, 8, 12), datetime.date(2026, 8, 13), 26),  # day after
        (datetime.date(2000, 2, 29), datetime.date(2026, 2, 28), 25),  # leap dob, not yet
        (datetime.date(2000, 2, 29), datetime.date(2026, 3, 1), 26),  # leap dob, passed
    ],
)
def test_age_at_is_exact_across_boundaries(dob, as_of, expected):
    customer = Customer(first_name="A", last_name="B", dob=dob)

    assert customer.age_at(as_of) == expected


@time_machine.travel(TODAY)
def test_age_property_uses_today():
    customer = Customer(first_name="Ben", last_name="Stokes", dob=datetime.date(1991, 6, 25))

    assert customer.age == 35


@pytest.mark.django_db
@time_machine.travel(TODAY)
def test_future_dob_is_rejected():
    customer = Customer(first_name="A", last_name="B", dob=datetime.date(2027, 1, 1))

    with pytest.raises(ValidationError):
        customer.full_clean()


@pytest.mark.django_db
@time_machine.travel(TODAY)
@pytest.mark.parametrize("dob", [datetime.date(2010, 1, 1), datetime.date(1900, 1, 1)])
def test_out_of_range_age_is_rejected(dob):
    customer = Customer(first_name="A", last_name="B", dob=dob)

    with pytest.raises(ValidationError):
        customer.full_clean()


def test_str_includes_full_name():
    customer = Customer(first_name="Ben", last_name="Stokes", dob=datetime.date(1991, 6, 25))

    assert str(customer) == "Ben Stokes"
