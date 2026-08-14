"""Quote/policy serializers: strict inputs, a read model that mirrors the diagram.

The dispatch inputs are deliberately narrow (`StrictFieldsMixin`) so a client
that sends `premium` is turned away rather than silently ignored (ADR-0004). The
read serializer renders exactly the shape the sequence diagram draws.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from apps.common.serializers import StrictFieldsMixin
from apps.customers.models import Customer
from apps.customers.serializers import CustomerSerializer
from apps.payments.models import Payment
from apps.policies.models import Policy, PolicyStateTransition
from apps.products.models import ProductType


class PaymentSummarySerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)

    class Meta:
        model = Payment
        fields = ["reference", "method", "amount", "currency", "status", "settled_at"]


class PolicyReadSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="product.code", read_only=True)
    premium = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=True, allow_null=True
    )
    cover = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Policy
        fields = [
            "id",
            "quote_reference",
            "customer_id",
            "type",
            "premium",
            "cover",
            "currency",
            "state",
            "rated_age",
            "quoted_at",
            "accepted_at",
            "activated_at",
            "quote_expires_at",
            "payment",
        ]

    @extend_schema_field(PaymentSummarySerializer(allow_null=True))
    def get_payment(self, obj: Policy):
        # Read from the prefetch cache (obj.payments.all()) so list views stay
        # free of N+1; pick the newest in Python rather than re-querying.
        payments = list(obj.payments.all())
        if not payments:
            return None
        latest = max(payments, key=lambda p: (p.created_at, p.id))
        return PaymentSummarySerializer(latest).data


class PolicyDetailSerializer(PolicyReadSerializer):
    """Detail view (diagram step 6): the read shape plus the nested customer."""

    customer = CustomerSerializer(read_only=True)

    class Meta(PolicyReadSerializer.Meta):
        fields = [*PolicyReadSerializer.Meta.fields, "customer", "rated_at"]


class TransitionSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = PolicyStateTransition
        fields = ["from_state", "to_state", "source", "actor", "reason", "at"]

    def get_actor(self, obj: PolicyStateTransition):
        return obj.actor.email if obj.actor_id else None


class QuoteCreateSerializer(StrictFieldsMixin, serializers.Serializer):
    """Diagram step 2 input: ``{customer_id, type}`` with optional ``cover``."""

    customer_id = serializers.IntegerField()
    type = serializers.SlugField()
    cover = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        try:
            attrs["customer"] = Customer.objects.get(pk=attrs["customer_id"])
        except Customer.DoesNotExist as exc:
            raise NotFound(f"No customer with id {attrs['customer_id']}.") from exc
        try:
            attrs["product"] = ProductType.objects.get(code=attrs["type"])
        except ProductType.DoesNotExist as exc:
            raise NotFound(f"No product with type '{attrs['type']}'.") from exc
        return attrs


class QuoteTransitionSerializer(StrictFieldsMixin, serializers.Serializer):
    """Diagram steps 3-4 input: ``{quote_id, status}`` with optional payment method."""

    quote_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=["accepted", "active"])
    payment_method = serializers.ChoiceField(
        choices=[Payment.Method.CARD, Payment.Method.INVOICE], required=False
    )
