"""Reusable serializer fields with no domain knowledge."""

from rest_framework import serializers


class FlexibleDateField(serializers.DateField):
    """A date field that accepts DD-MM-YYYY (the brief) and ISO on input, and
    always renders DD-MM-YYYY on output (D2, ADR-0005).

    Input formats are ordered DD-MM-YYYY first so the brief's own ``25-06-1991``
    parses unambiguously; ISO ``YYYY-MM-DD`` is accepted as a convenience.
    """

    INPUT_FORMATS = ("%d-%m-%Y", "%Y-%m-%d")
    OUTPUT_FORMAT = "%d-%m-%Y"

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", self.INPUT_FORMATS)
        kwargs.setdefault("format", self.OUTPUT_FORMAT)
        super().__init__(**kwargs)
