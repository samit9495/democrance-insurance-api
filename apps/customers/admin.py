"""Customer admin (REQUIREMENTS 10, REQ-P1-6).

Policy count and the read-only policy inline are added in Phase 10 once the
Policy model exists; this class already satisfies "customer visible, correct
and searchable".
"""

from django.contrib import admin

from apps.customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "dob", "display_age")
    search_fields = ("first_name", "last_name", "email", "id")
    list_filter = ("created_at",)
    readonly_fields = ("reference", "created_at", "updated_at")
    ordering = ("last_name", "first_name")

    @admin.display(description="Age")
    def display_age(self, obj: Customer) -> int:
        return obj.age
