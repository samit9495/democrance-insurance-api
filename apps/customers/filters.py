"""Customer search filters (Part 3, REQUIREMENTS 8.2, D8).

Partial case-insensitive name matching, a free-text ``q`` across either name, a
``dob`` that accepts both the brief's DD-MM-YYYY and ISO, and ``policy_type`` to
find customers who hold a policy of a given product. Filters combine with AND.
"""

from __future__ import annotations

import datetime

import django_filters
from django.db.models import Q

from apps.customers.models import Customer

_DATE_FORMATS = ("%d-%m-%Y", "%Y-%m-%d")


def parse_flexible_date(value: str) -> datetime.date | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


class CustomerFilterSet(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")
    dob = django_filters.CharFilter(method="filter_dob")
    policy_type = django_filters.CharFilter(field_name="policies__product__code", distinct=True)
    q = django_filters.CharFilter(method="filter_q")

    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "dob", "policy_type", "q"]

    def filter_dob(self, queryset, name, value):
        parsed = parse_flexible_date(value)
        return queryset.none() if parsed is None else queryset.filter(dob=parsed)

    def filter_q(self, queryset, name, value):
        return queryset.filter(Q(first_name__icontains=value) | Q(last_name__icontains=value))
