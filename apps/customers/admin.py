"""Customer admin (REQUIREMENTS 10, REQ-P1-6): searchable, with a read-only
inline of the customer's policies and a policy count."""

from django.contrib import admin

from apps.customers.models import Customer
from apps.policies.models import Policy


class PolicyInline(admin.TabularInline):
    model = Policy
    extra = 0
    can_delete = False
    fields = ("id", "quote_reference", "product", "state", "premium", "cover")
    readonly_fields = fields
    show_change_link = True

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "dob", "display_age", "policy_count")
    search_fields = ("first_name", "last_name", "email", "id")
    list_filter = ("created_at",)
    readonly_fields = ("reference", "created_at", "updated_at")
    ordering = ("last_name", "first_name")
    inlines = [PolicyInline]

    @admin.display(description="Age")
    def display_age(self, obj: Customer) -> int:
        return obj.age

    @admin.display(description="Policies")
    def policy_count(self, obj: Customer) -> int:
        return obj.policies.count()
