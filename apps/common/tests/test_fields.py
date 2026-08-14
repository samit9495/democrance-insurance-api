"""Phase 2: FlexibleDateField (D2, ADR-0005).

Accepts DD-MM-YYYY (the brief) and ISO on input; always renders DD-MM-YYYY.
"""

import datetime

import pytest
from rest_framework import serializers

from apps.common.fields import FlexibleDateField


@pytest.mark.parametrize("value", ["25-06-1991", "1991-06-25"])
def test_parses_accepted_input_formats(value):
    field = FlexibleDateField()

    assert field.to_internal_value(value) == datetime.date(1991, 6, 25)


@pytest.mark.parametrize(
    "value",
    ["1991-25-06", "31-02-1991", "25/06/1991", "yesterday", ""],
)
def test_rejects_invalid_input(value):
    field = FlexibleDateField()

    with pytest.raises(serializers.ValidationError):
        field.to_internal_value(value)


def test_renders_ddmmyyyy_on_output():
    field = FlexibleDateField()

    assert field.to_representation(datetime.date(1991, 6, 25)) == "25-06-1991"
