"""Policy filtering for the list endpoint (REQUIREMENTS 8.1 step 5, REQ-P3-4).

Phase 7 wires the filters the diagram's list call needs (`customer_id`, `state`,
`type`, created-at window); Phase 8 builds on this set for Part 3 search.
"""

import django_filters

from apps.policies.models import Policy


class PolicyFilterSet(django_filters.FilterSet):
    customer_id = django_filters.NumberFilter(field_name="customer_id")
    type = django_filters.CharFilter(field_name="product__code")
    created_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Policy
        fields = ["customer_id", "state", "type", "created_after", "created_before"]
