"""Quote HTTP surface: one overloaded /quote/ dispatcher plus clean REST aliases.

Views stay thin — they validate the request shape and delegate to the policy and
payment services, which own every state change (ADR-0002). The dispatcher and
the aliases share the same three handlers so their behaviour cannot drift.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments.models import Payment
from apps.payments.services import simulate_payment
from apps.policies import services
from apps.policies.models import Policy
from apps.policies.serializers import (
    PolicyReadSerializer,
    QuoteCreateSerializer,
    QuoteTransitionSerializer,
)


def _actor(request):
    return request.user if request.user.is_authenticated else None


def _get_policy(quote_id: int) -> Policy:
    try:
        return Policy.objects.select_related("product", "customer").get(pk=quote_id)
    except Policy.DoesNotExist as exc:
        raise NotFound(f"No quote with id {quote_id}.") from exc


def _render(policy: Policy, *, http_status: int = status.HTTP_200_OK) -> Response:
    return Response(PolicyReadSerializer(policy).data, status=http_status)


def _create_quote(data, actor=None) -> Response:
    serializer = QuoteCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    v = serializer.validated_data
    policy = services.create_quote(
        customer=v["customer"], product=v["product"], cover=v.get("cover"), actor=actor
    )
    return _render(policy, http_status=status.HTTP_201_CREATED)


def _accept_quote(quote_id: int, actor=None) -> Response:
    policy = services.accept_quote(policy=_get_policy(quote_id), actor=actor)
    return _render(policy)


def _pay_quote(quote_id: int, payment_method: str | None, actor=None) -> Response:
    policy = _get_policy(quote_id)
    simulate_payment(policy=policy, method=payment_method or Payment.Method.CARD, actor=actor)
    policy.refresh_from_db()
    return _render(policy)


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
            return _create_quote(data, actor=_actor(request))
        if has_transition:
            serializer = QuoteTransitionSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            v = serializer.validated_data
            actor = _actor(request)
            if v["status"] == "accepted":
                return _accept_quote(v["quote_id"], actor=actor)
            return _pay_quote(v["quote_id"], v.get("payment_method"), actor=actor)

        raise ValidationError(
            "Unrecognised payload: send customer_id+type to create a quote, "
            "or quote_id+status to accept or pay one."
        )


class QuoteCollectionView(APIView):
    """REST alias for creation: ``POST /api/v1/quotes/``."""

    def post(self, request):
        return _create_quote(request.data, actor=_actor(request))


class QuoteAcceptView(APIView):
    """REST alias: ``POST /api/v1/quotes/<id>/accept/``."""

    def post(self, request, pk):
        return _accept_quote(pk, actor=_actor(request))


class QuotePayView(APIView):
    """REST alias: ``POST /api/v1/quotes/<id>/pay/``."""

    def post(self, request, pk):
        method = request.data.get("payment_method") if isinstance(request.data, dict) else None
        return _pay_quote(pk, method, actor=_actor(request))
