"""Phase 2: CustomerSerializer validation and representation."""

import datetime

import pytest
import time_machine

from apps.customers.serializers import CustomerSerializer

TODAY = datetime.date(2026, 8, 13)
BRIEF_PAYLOAD = {"first_name": "Ben", "last_name": "Stokes", "dob": "25-06-1991"}


@pytest.mark.parametrize("missing", ["first_name", "last_name", "dob"])
def test_required_fields_are_enforced(missing):
    payload = dict(BRIEF_PAYLOAD)
    payload.pop(missing)

    serializer = CustomerSerializer(data=payload)

    assert not serializer.is_valid()
    assert missing in serializer.errors


@time_machine.travel(TODAY)
def test_whitespace_is_stripped_from_names():
    serializer = CustomerSerializer(
        data={"first_name": "  Ben  ", "last_name": " Stokes ", "dob": "25-06-1991"}
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["first_name"] == "Ben"
    assert serializer.validated_data["last_name"] == "Stokes"


def test_unknown_fields_are_rejected():
    serializer = CustomerSerializer(data={**BRIEF_PAYLOAD, "premium": "5.00"})

    assert not serializer.is_valid()
    assert "premium" in serializer.errors


@pytest.mark.django_db
@time_machine.travel(TODAY)
def test_age_is_read_only_and_computed():
    serializer = CustomerSerializer(data={**BRIEF_PAYLOAD, "age": 99})

    assert serializer.is_valid(), serializer.errors
    serializer.save()

    assert serializer.data["age"] == 35
