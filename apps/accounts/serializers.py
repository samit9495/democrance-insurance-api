"""Auth serializers. The token pair uses simplejwt's default; ``/me/`` exposes
the principal's role and the linked customer id (REQUIREMENTS 8.3)."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    role = serializers.CharField(read_only=True)
    customer_id = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.INT)
    def get_customer_id(self, obj):
        profile = getattr(obj, "customer_profile", None)
        return profile.id if profile is not None else None
