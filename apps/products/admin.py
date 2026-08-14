"""Products admin — editable catalogue and rating rules (REQUIREMENTS 10).

Overlap validation lives in ``RatingRule.clean()``; the admin ModelForm runs it
on save, so a clashing band is surfaced as a form error rather than a 500.
"""

from django.contrib import admin

from apps.products.models import ProductType, RatingRule


class RatingRuleInline(admin.TabularInline):
    model = RatingRule
    extra = 0


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "default_cover", "min_cover", "max_cover")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    inlines = [RatingRuleInline]


@admin.register(RatingRule)
class RatingRuleAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "age_band_min",
        "age_band_max",
        "rate_per_1000_cover",
        "min_premium",
        "valid_from",
        "valid_to",
        "is_active",
    )
    list_filter = ("product", "is_active")
    search_fields = ("product__code",)
