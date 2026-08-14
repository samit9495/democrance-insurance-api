"""Quote HTTP surface: one overloaded /quote/ dispatcher plus clean REST aliases.

Views stay thin — they validate the request shape and delegate to the policy and
payment services, which own every state change (ADR-0002). The dispatcher and
the aliases share the same three handlers so their behaviour cannot drift.
"""

from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import scope_policies
from apps.payments.models import Payment
from apps.payments.services import simulate_payment
from apps.policies import services
from apps.policies.filters import PolicyFilterSet
from apps.policies.models import Policy
from apps.policies.serializers import (
    PolicyDetailSerializer,
    PolicyReadSerializer,
    QuoteCreateSerializer,
    QuoteTransitionSerializer,
    TransitionSerializer,
)


def _policy_queryset():
    return Policy.objects.select_related("product", "customer").prefetch_related("payments")


def _actor(user):
    return user if user and user.is_authenticated else None


def _get_policy(quote_id: int, user) -> Policy:
    # Scope first, so a customer asking for someone else's quote gets 404 (not 403).
    try:
        return scope_policies(_policy_queryset(), user).get(pk=quote_id)
    except Policy.DoesNotExist as exc:
        raise NotFound(f"No quote with id {quote_id}.") from exc


def _render(policy: Policy, *, http_status: int = status.HTTP_200_OK) -> Response:
    return Response(PolicyReadSerializer(policy).data, status=http_status)


def _create_quote(data, user) -> Response:
    serializer = QuoteCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    v = serializer.validated_data
    customer = v["customer"]
    # A customer principal may only act for itself — anyone else's id is "not found".
    if user and user.is_authenticated and user.is_customer and customer.user_id != user.id:
        raise NotFound(f"No customer with id {customer.id}.")
    policy = services.create_quote(
        customer=customer, product=v["product"], cover=v.get("cover"), actor=_actor(user)
    )
    return _render(policy, http_status=status.HTTP_201_CREATED)


def _accept_quote(quote_id: int, user) -> Response:
    policy = services.accept_quote(policy=_get_policy(quote_id, user), actor=_actor(user))
    return _render(policy)


def _pay_quote(quote_id: int, payment_method: str | None, user) -> Response:
    policy = _get_policy(quote_id, user)
    simulate_payment(
        policy=policy, method=payment_method or Payment.Method.CARD, actor=_actor(user)
    )
    policy.refresh_from_db()
    return _render(policy)


@extend_schema(request=QuoteCreateSerializer, responses=PolicyReadSerializer)
class QuoteDispatchView(APIView):
    """The diagram's single ``POST /api/v1/quote/`` doing create / accept / pay."""

    def post(self, request):
        data = request.data
        if not isinstance(data, dict):
            raise ValidationError("Expected a JSON object.")

        has_create = "customer_id" in data or "type" in data
        has_transition = "quote_id" in data or "status" in data

        if has_create and has_transition:
            raise ValidationError(
                "Ambiguous payload: send customer_id+type to create a quote, "
                "or quote_id+status to accept or pay one — not both."
            )
        if has_create:
            return _create_quote(data, request.user)
        if has_transition:
            serializer = QuoteTransitionSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            v = serializer.validated_data
            if v["status"] == "accepted":
                return _accept_quote(v["quote_id"], request.user)
            return _pay_quote(v["quote_id"], v.get("payment_method"), request.user)

        raise ValidationError(
            "Unrecognised payload: send customer_id+type to create a quote, "
            "or quote_id+status to accept or pay one."
        )


@extend_schema(request=QuoteCreateSerializer, responses=PolicyReadSerializer)
class QuoteCollectionView(APIView):
    """REST alias for creation: ``POST /api/v1/quotes/``."""

    def post(self, request):
        return _create_quote(request.data, request.user)


@extend_schema(request=None, responses=PolicyReadSerializer)
class QuoteAcceptView(APIView):
    """REST alias: ``POST /api/v1/quotes/<id>/accept/``."""

    def post(self, request, pk):
        return _accept_quote(pk, request.user)


@extend_schema(request=QuoteTransitionSerializer, responses=PolicyReadSerializer)
class QuotePayView(APIView):
    """REST alias: ``POST /api/v1/quotes/<id>/pay/``."""

    def post(self, request, pk):
        method = request.data.get("payment_method") if isinstance(request.data, dict) else None
        return _pay_quote(pk, method, request.user)


class PolicyListView(generics.ListAPIView):
    """Diagram step 5: ``GET /api/v1/policies/?customer_id=...``, paginated + scoped."""

    serializer_class = PolicyReadSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PolicyFilterSet
    ordering_fields = ["created_at", "premium", "state"]
    ordering = ["-created_at", "-id"]

    def get_queryset(self):
        return scope_policies(_policy_queryset(), self.request.user)


class PolicyDetailView(generics.RetrieveAPIView):
    """Diagram step 6: ``GET /api/v1/policies/<id>/`` with the nested customer."""

    serializer_class = PolicyDetailSerializer

    def get_queryset(self):
        return scope_policies(_policy_queryset(), self.request.user)

    def handle_exception(self, exc):
        from django.http import Http404

        if isinstance(exc, Http404):
            exc = NotFound(f"No policy with id {self.kwargs.get('pk')}.")
        return super().handle_exception(exc)


@extend_schema(responses=OpenApiTypes.OBJECT)
class PolicyHistoryView(APIView):
    """Diagram step 7: ``GET /api/v1/policies/<id>/history/`` — the full narrative."""

    def get(self, request, pk):
        policy = _get_policy(pk, request.user)
        transitions = policy.transitions.select_related("actor").all()
        return Response(
            {
                "policy_id": policy.id,
                "current_state": policy.state,
                "transitions": TransitionSerializer(transitions, many=True).data,
            }
        )
