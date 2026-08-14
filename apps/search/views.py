"""Unified search spanning customers and policies in one call (REQUIREMENTS 8.2).

``GET /api/v1/search/?q=...&entity=all|customers|policies`` returns each entity
with its own count and (capped) results. All matching is done through the ORM,
so a hostile ``q`` is parameterised and cannot inject SQL.
"""

from __future__ import annotations

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import scope_customers, scope_policies
from apps.customers.models import Customer
from apps.customers.serializers import CustomerSerializer
from apps.policies.models import Policy
from apps.policies.serializers import PolicyReadSerializer

_LIMIT = 20
_ENTITIES = ("all", "customers", "policies")


@extend_schema(
    parameters=[
        OpenApiParameter("q", OpenApiTypes.STR, description="Free-text query."),
        OpenApiParameter("entity", OpenApiTypes.STR, enum=list(_ENTITIES)),
    ],
    responses=OpenApiTypes.OBJECT,
)
class SearchView(APIView):
    def get(self, request):
        entity = request.query_params.get("entity", "all")
        if entity not in _ENTITIES:
            raise ValidationError({"entity": f"Must be one of: {', '.join(_ENTITIES)}."})

        q = request.query_params.get("q", "").strip()
        user = request.user
        payload: dict = {}
        if entity in ("all", "customers"):
            payload["customers"] = self._section(self._customers(q, user), CustomerSerializer)
        if entity in ("all", "policies"):
            payload["policies"] = self._section(self._policies(q, user), PolicyReadSerializer)
        return Response(payload)

    @staticmethod
    def _customers(q: str, user):
        qs = scope_customers(Customer.objects.all(), user)
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))
        return qs

    @staticmethod
    def _policies(q: str, user):
        qs = scope_policies(
            Policy.objects.select_related("product", "customer").prefetch_related("payments"),
            user,
        )
        if q:
            qs = qs.filter(
                Q(quote_reference__icontains=q)
                | Q(customer__first_name__icontains=q)
                | Q(customer__last_name__icontains=q)
            )
        return qs

    @staticmethod
    def _section(queryset, serializer_cls) -> dict:
        return {
            "count": queryset.count(),
            "results": serializer_cls(queryset[:_LIMIT], many=True).data,
        }
