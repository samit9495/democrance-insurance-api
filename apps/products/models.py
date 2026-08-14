"""Product catalogue and date-versioned rating rules (REQUIREMENTS 6.3/6.4, ADR-0006)."""

from __future__ import annotations

import datetime
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.common.models import TimeStampedModel


def default_currency() -> str:
    return getattr(settings, "DEFAULT_CURRENCY", "AED")


class ProductType(TimeStampedModel):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    default_cover = models.DecimalField(max_digits=12, decimal_places=2)
    min_cover = models.DecimalField(max_digits=12, decimal_places=2)
    max_cover = models.DecimalField(max_digits=12, decimal_places=2)

    min_age = models.PositiveSmallIntegerField(default=18)
    max_age = models.PositiveSmallIntegerField(default=100)

    currency = models.CharField(max_length=3, default=default_currency)

    class Meta:
        ordering = ("code",)

    def __str__(self) -> str:
        return self.code


class RatingRule(TimeStampedModel):
    product = models.ForeignKey(ProductType, on_delete=models.CASCADE, related_name="rating_rules")
    age_band_min = models.PositiveSmallIntegerField()
    age_band_max = models.PositiveSmallIntegerField()
    rate_per_1000_cover = models.DecimalField(max_digits=6, decimal_places=4)
    loading_factor = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("1.0000"))
    min_premium = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("product", "age_band_min", "-valid_from")
        constraints = [
            models.CheckConstraint(
                condition=Q(age_band_min__lte=F("age_band_max")),
                name="rating_age_band_min_lte_max",
            ),
        ]

    def __str__(self) -> str:
        band = f"{self.age_band_min}-{self.age_band_max}"
        return f"{self.product_id} {band} @ {self.rate_per_1000_cover}"

    def covers_age(self, age: int) -> bool:
        return self.age_band_min <= age <= self.age_band_max

    def is_effective_on(self, as_of: datetime.date) -> bool:
        if self.valid_from > as_of:
            return False
        return self.valid_to is None or self.valid_to >= as_of

    def clean(self) -> None:
        super().clean()
        if self.age_band_min is None or self.age_band_max is None:
            return
        if self.age_band_min > self.age_band_max:
            raise ValidationError({"age_band_max": "age_band_max must be >= age_band_min."})
        if not self.is_active:
            return

        others = RatingRule.objects.filter(product=self.product, is_active=True)
        if self.pk:
            others = others.exclude(pk=self.pk)
        for other in others:
            if self._age_ranges_overlap(other) and self._windows_overlap(other):
                raise ValidationError(
                    "Overlapping active rating band for this product and validity window."
                )

    def _age_ranges_overlap(self, other: RatingRule) -> bool:
        return not (
            self.age_band_max < other.age_band_min or other.age_band_max < self.age_band_min
        )

    def _windows_overlap(self, other: RatingRule) -> bool:
        self_to = self.valid_to or datetime.date.max
        other_to = other.valid_to or datetime.date.max
        return self.valid_from <= other_to and other.valid_from <= self_to
