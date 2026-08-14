"""Customer serializers (REQUIREMENTS 8.1)."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.common.fields import FlexibleDateField
from apps.common.serializers import StrictFieldsMixin
from apps.customers.models import Customer


class CustomerSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    dob = FlexibleDateField()
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "reference",
            "first_name",
            "last_name",
            "dob",
            "age",
            "email",
            "phone",
            "created_at",
        ]
        read_only_fields = ["id", "reference", "created_at"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Run the model's domain rules (past dob, age band) at the serializer
        # boundary so violations surface as a 400, not a 500.
        probe = Customer(
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
            dob=attrs.get("dob"),
        )
        try:
            probe.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return attrs
