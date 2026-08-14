"""Shared serializer helpers."""

from rest_framework import serializers


class StrictFieldsMixin:
    """Reject unknown top-level keys instead of silently ignoring them.

    DRF drops unrecognised input by default; for a small, explicit contract it
    is safer to tell the client exactly which field it got wrong (this is also
    how a client-supplied ``premium`` is turned away — ADR-0004).
    """

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(dict.fromkeys(sorted(unknown), "Unknown field."))
        return super().to_internal_value(data)
