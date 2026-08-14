"""Read-only admin for payments: receipts are observed, never hand-edited."""

from django.contrib import admin

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "policy",
        "method",
        "amount",
        "currency",
        "status",
        "settled_at",
        "created_at",
    )
    list_filter = ("method", "status", "currency")
    search_fields = ("reference", "idempotency_key", "policy__quote_reference")
    readonly_fields = tuple(f.name for f in Payment._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
