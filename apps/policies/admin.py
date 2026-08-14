"""Policy admin (REQUIREMENTS 10, REQ-P2-6).

State is never hand-edited: it is read-only, and the two actions route through
the same service layer as the API, so admin changes are validated and audited
(``source="admin"``). Transition history is shown inline, read-only.
"""

from __future__ import annotations

from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from apps.common.exceptions import DomainError
from apps.policies import services
from apps.policies.models import Policy, PolicyStateTransition


class PolicyStateTransitionInline(admin.TabularInline):
    model = PolicyStateTransition
    extra = 0
    can_delete = False
    fields = ("from_state", "to_state", "source", "actor", "reason", "created_at")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "quote_reference",
        "customer_link",
        "type",
        "state",
        "premium",
        "cover",
        "created_at",
    )
    list_filter = ("state", "product", "created_at")
    search_fields = ("id", "quote_reference", "customer__first_name", "customer__last_name")
    autocomplete_fields = ("customer",)
    readonly_fields = (
        "quote_reference",
        "state",
        "premium",
        "currency",
        "rating_rule",
        "rated_age",
        "rated_at",
        "quoted_at",
        "accepted_at",
        "activated_at",
        "quote_expires_at",
        "created_at",
        "updated_at",
    )
    inlines = [PolicyStateTransitionInline]
    actions = ["accept_selected_quotes", "bind_selected_policies"]

    @admin.display(description="Type")
    def type(self, obj: Policy) -> str:
        return obj.product.code

    @admin.display(description="Customer")
    def customer_link(self, obj: Policy):
        url = reverse("admin:customers_customer_change", args=[obj.customer_id])
        return format_html('<a href="{}">{}</a>', url, obj.customer)

    def _run(self, request, queryset, fn, verb: str) -> None:
        done = 0
        for policy in queryset:
            try:
                fn(policy=policy, actor=request.user, source="admin")
                done += 1
            except DomainError as exc:
                self.message_user(request, f"{policy}: {exc.detail}", level=messages.ERROR)
        if done:
            self.message_user(request, f"{verb} {done} policy/policies.")

    @admin.action(description="Accept selected quotes")
    def accept_selected_quotes(self, request, queryset):
        self._run(request, queryset, services.accept_quote, "Accepted")

    @admin.action(description="Bind selected policies")
    def bind_selected_policies(self, request, queryset):
        self._run(request, queryset, services.activate_policy, "Bound")


@admin.register(PolicyStateTransition)
class PolicyStateTransitionAdmin(admin.ModelAdmin):
    list_display = ("id", "policy", "from_state", "to_state", "source", "actor", "created_at")
    list_filter = ("source", "to_state")
    search_fields = ("policy__id", "policy__quote_reference")
    readonly_fields = tuple(f.name for f in PolicyStateTransition._meta.fields)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
