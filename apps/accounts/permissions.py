"""Authorisation: deny by default, with a loud demo escape hatch (D4, ADR-0008).

Two permission classes plus queryset-scoping helpers. Scoping is done in
``get_queryset`` so a customer principal receives 404 (not 403) for records it
may not see — no existence leakage (REQUIREMENTS 9.2).
"""

from __future__ import annotations

from django.conf import settings
from rest_framework.permissions import BasePermission


def demo_open() -> bool:
    return bool(getattr(settings, "DEMO_OPEN_API", False))


class DemoOrAuthenticated(BasePermission):
    """Allow any authenticated principal; allow anonymous only in demo mode."""

    def has_permission(self, request, view) -> bool:
        if request.user and request.user.is_authenticated:
            return True
        return demo_open()


class DemoOrStaff(BasePermission):
    """Staff/agent only. Anonymous is allowed solely in demo mode; an
    authenticated customer is always refused (customers cannot create customers)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if user and user.is_authenticated:
            return user.is_agent_or_staff
        return demo_open()


def scope_customers(queryset, user):
    """Narrow a Customer queryset to what ``user`` may see."""
    if not user or not user.is_authenticated or user.is_agent_or_staff:
        return queryset
    return queryset.filter(user=user)


def scope_policies(queryset, user):
    """Narrow a Policy queryset to what ``user`` may see."""
    if not user or not user.is_authenticated or user.is_agent_or_staff:
        return queryset
    return queryset.filter(customer__user=user)
